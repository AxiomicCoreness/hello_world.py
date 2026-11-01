// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/*
 * ============================================================================
 * XCODE INTEGRATION NOTES
 * ============================================================================
 * 1. This file lives in ios/ClarkePocket/Sources/PocketCore, which project.yml (XcodeGen)
 *    compiles straight into the ClarkePocket app target. No manual drag-and-drop needed.
 * 2. Companion files in the same folder: ClarkeGGUF.swift (GGUF reader + dequant),
 *    ClarkeTokenizer.swift (byte-level BPE from GGUF metadata), ClarkeQwen2.swift (decoder).
 * 3. `swift test` in ios/ClarkePocket runs the offline tests on a Mac or Linux
 *    (Tests/PocketCoreTests/ClarkeEngineTests.swift: synthetic GGUF fixtures, no model weights).
 * 4. Target iOS 16.4+ (same as the app).
 * 5. The app wraps this engine as the ChatEngine `ClarkeChatEngine` (ClarkePocket/ChatEngine.swift).
 *    Engine order: MLX (primary) -> ClarkeEngine (Clarke Yoursa Tee's own) -> llama.cpp (fallback).
 *
 * NOTE ON THE MODEL:
 * - Reads Clarke Yoursa Tee's own pinned GGUF (ModelPin: deepseek-r2-1.5b Q4_K_M, qwen2
 *   architecture) from disk via mmap. Hyperparameters, tokenizer and merges come from the file.
 * - Model files are never committed; tests generate tiny GGUF files in a temp directory.
 *
 * NOTE ON GPU / CUDA:
 * - No Metal and no CUDA in this target. CPU only: Foundation + Accelerate (vDSP) on Apple
 *   platforms, plain Swift loops on Linux. Speed figures are whatever the device measured.
 * - syncWithGate uses HTTPS JSON (plain http only to 127.0.0.1, for local testing).
 * ============================================================================
 */

struct ClarkeEngine {
    // §0 Constants (Defaults if the gate is offline; qwen2 hyperparameters are re-read from the
    //    model file on load, these only fill keys a file leaves out)
    static var config = Qwen2Hyperparameters(
        nLayer: 28,          // n_layer
        nEmbd: 1536,         // n_embd
        nHead: 12,           // n_head
        nHeadKV: 2,          // n_head_kv
        nFF: 8960,           // feed_forward_length
        ropeBase: 1_000_000, // rope base 1e6
        rmsEps: 1e-6,        // rms eps
        nVocab: 151_936,     // vocab
        nCtxTrain: 131_072)
    static var contextTokens = 2048
    static var temperature: Float = 0.6
    static let engineName = "ClarkeEngine (pure Swift qwen2, CPU)"

    /// The pinned model, as the gate describes it (defaults: ModelPin).
    struct ModelManifest: Codable, Equatable {
        var name: String
        var sha256: String
        var sizeBytes: Int64

        enum CodingKeys: String, CodingKey { case name, sha256, sizeBytes = "size_bytes" }

        /// Strict check: .gguf name, 64 lower-case hex digest, positive size.
        func validated() throws -> ModelManifest {
            let hex = sha256.lowercased()
            guard name.hasSuffix(".gguf"), !name.contains("/"),
                  hex.count == 64, hex.allSatisfy({ $0.isHexDigit }), sizeBytes > 0
            else { throw GateError.badManifest }
            return ModelManifest(name: name, sha256: hex, sizeBytes: sizeBytes)
        }
    }
    static var pinnedModel = ModelManifest(name: ModelPin.fileName, sha256: ModelPin.sha256, sizeBytes: ModelPin.sizeBytes)

    enum GateError: Error, Equatable { case insecureURL, badManifest, http(Int) }
    enum GateSync: Equatable { case updated(ModelManifest), offlineDefaults(String) }

    /// Manifest URL under the gate base.
    static func manifestURL(base: URL) throws -> URL {
        let scheme = base.scheme?.lowercased()
        let loopback = scheme == "http" && base.host == "127.0.0.1"
        guard scheme == "https" || loopback else { throw GateError.insecureURL }
        return base.appendingPathComponent("clarke-engine").appendingPathComponent("model-manifest.json")
    }

    /// Fetch the pinned model manifest (name, full sha256, size) as JSON from the gate and update
    /// `pinnedModel`. Offline / unreachable: keeps the defaults and returns `.offlineDefaults`.
    /// A reachable gate that returns a bad manifest throws and changes nothing.
    @discardableResult
    static func syncWithGate(base: URL, session: URLSession = .shared) async throws -> GateSync {
        let url = try manifestURL(base: base)
        var req = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 10)
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        let data: Data
        let resp: URLResponse
        do {
            (data, resp) = try await fetch(session, req)
        } catch {
            return .offlineDefaults("gate unreachable: \(error.localizedDescription)")
        }
        if let h = resp as? HTTPURLResponse, h.statusCode != 200 { throw GateError.http(h.statusCode) }
        let m: ModelManifest
        do { m = try JSONDecoder().decode(ModelManifest.self, from: data).validated() } catch { throw GateError.badManifest }
        pinnedModel = m
        return .updated(m)
    }

    private static func fetch(_ s: URLSession, _ r: URLRequest) async throws -> (Data, URLResponse) {
        try await withCheckedThrowingContinuation { c in
            s.dataTask(with: r) { d, resp, e in
                if let e { c.resume(throwing: e) }
                else if let d, let resp { c.resume(returning: (d, resp)) }
                else { c.resume(throwing: URLError(.badServerResponse)) }
            }.resume()
        }
    }

    struct EngineResults: Equatable {
        let engineName: String
        let modelSHA256: String     // pinned digest (download verified by ModelStore)
        let modelSizeMatchesPin: Bool
        let promptTokens: Int
        let tokens: [Int32]         // generated
        let text: String
        let seconds: Double
        /// Measured on whatever hardware ran this (CI runner, Mac, iPhone).
        let tokensPerSecond: Double
    }

    /// Load the model at `modelPath` and generate an answer to `user`, for real. Prompt format:
    /// ChatML when the vocabulary has <|im_start|> as a special token; otherwise the model's own
    /// DeepSeek turn markers (the pinned 1.5B GGUF has those, not ChatML).
    static func run(modelPath: String, system: String = "", user: String,
                    maxTokens: Int = 64, temperature: Float? = nil, seed: UInt64 = 0) throws -> EngineResults {
        let s = try Session(modelPath: modelPath, nCtx: contextTokens)
        let turns = [PromptTurn(role: "system", content: system), PromptTurn(role: "user", content: user)]
        let start = Date()
        let n = try s.begin(turns, maxTokens: maxTokens, temperature: temperature ?? self.temperature, seed: seed)
        var text = ""
        while let piece = try s.next() { text += piece }
        let secs = Date().timeIntervalSince(start)
        let size = FileVerifier.fileSize(URL(fileURLWithPath: modelPath))
        return EngineResults(engineName: engineName, modelSHA256: pinnedModel.sha256,
                             modelSizeMatchesPin: size == pinnedModel.sizeBytes,
                             promptTokens: n, tokens: s.generated, text: text, seconds: secs,
                             tokensPerSecond: secs > 0 ? Double(s.generated.count) / secs : 0)
    }

    /// Streaming session used by the app's ChatEngine adapter.
    final class Session {
        let model: Qwen2Model
        let tokenizer: ClarkeTokenizer
        let stopIDs: Set<Int32>
        private(set) var generated: [Int32] = []
        private var logits: [Float] = []
        private var budget = 0
        private var sampler = ClarkeSampler(temperature: 0, seed: 0)
        private var pieces = UTF8PieceBuffer()
        private var cancelled = false

        init(modelPath: String, nCtx: Int) throws {
            let g = try GGUFFile(path: modelPath)
            model = try Qwen2Model(gguf: g, fallback: ClarkeEngine.config, nCtx: nCtx)
            tokenizer = try ClarkeTokenizer(gguf: g)
            var stops = Set<Int32>()
            if let e = tokenizer.eosID { stops.insert(e) }
            for t in ["<|im_end|>", "<|endoftext|>", "<｜end▁of▁sentence｜>"] { if let id = tokenizer.id(t) { stops.insert(id) } }
            stopIDs = stops
            ClarkeEngine.config = model.hp
        }

        /// ChatML (`<|im_start|>role ... <|im_end|>`). Used when the vocabulary has <|im_start|> as
        /// a special token.
        static func chatML(_ turns: [PromptTurn]) -> String {
            var s = ""
            for t in turns where !(t.role == "system" && t.content.isEmpty) {
                s += "<|im_start|>\(t.role)\n\(t.content)<|im_end|>\n"
            }
            return s + "<|im_start|>assistant\n"
        }

        /// The DeepSeek-R1-distill turn markers. Clarke Yoursa Tee's pinned 1.5B GGUF has these as
        /// special tokens and no <|im_start|>, so ChatML would be read there as plain text.
        static func deepSeek(_ turns: [PromptTurn], bos: String) -> String {
            var s = bos
            for t in turns where t.role == "system" { s += t.content }
            for t in turns {
                if t.role == "user" { s += "<｜User｜>" + t.content }
                if t.role == "assistant" { s += "<｜Assistant｜>" + t.content + "<｜end▁of▁sentence｜>" }
            }
            return s + "<｜Assistant｜>"
        }

        enum PromptFormat: Equatable { case chatML, deepSeek }
        static func format(for tok: ClarkeTokenizer) -> PromptFormat {
            if tok.isSpecial("<|im_start|>") { return .chatML }
            if tok.isSpecial("<｜User｜>"), tok.isSpecial("<｜Assistant｜>") { return .deepSeek }
            return .chatML
        }

        func render(_ turns: [PromptTurn]) -> String {
            switch Self.format(for: tokenizer) {
            case .chatML: return Self.chatML(turns)
            case .deepSeek:
                let bos = tokenizer.bosID.flatMap { $0 >= 0 && Int($0) < tokenizer.count ? tokenizer.tokens[Int($0)] : nil } ?? ""
                return Self.deepSeek(turns, bos: bos)
            }
        }

        func tokenCount(_ turns: [PromptTurn]) -> Int { tokenizer.encode(render(turns)).count }

        /// Prefill the prompt; returns its token count.
        func begin(_ turns: [PromptTurn], maxTokens: Int, temperature: Float, seed: UInt64) throws -> Int {
            let ids = tokenizer.encode(render(turns))
            guard !ids.isEmpty else { throw GGUFError.shape("empty prompt") }
            guard ids.count + 1 < model.nCtx else { throw GGUFError.shape("prompt \(ids.count) tokens > context \(model.nCtx)") }
            model.reset()
            generated = []
            pieces = UTF8PieceBuffer()
            cancelled = false
            sampler = ClarkeSampler(temperature: temperature, seed: seed)
            budget = Swift.min(maxTokens, model.nCtx - ids.count - 1)
            for id in ids { logits = try model.forward(token: id) }
            return ids.count
        }

        /// Next text piece (may be "" mid-character), or nil when finished.
        func next() throws -> String? {
            if cancelled || generated.count >= budget || logits.isEmpty { return nil }
            let tok = sampler.sample(logits)
            if stopIDs.contains(tok) { logits = []; return nil }
            generated.append(tok)
            let piece = pieces.push(tokenizer.bytes(tok))
            if generated.count < budget { logits = try model.forward(token: tok) }
            return piece
        }

        func cancel() { cancelled = true }
    }
}
