// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// One protocol for the three on-device engines, in selection order:
//   1. MLXEngine  (PRIMARY): MLX Swift + Clarke Yoursa Tee's own MLX-converted model (MLXModelPin).
//   2. ClarkeChatEngine: ClarkeEngine (PocketCore/ClarkeEngine.swift), Clarke Yoursa Tee's own
//      pure-Swift qwen2 engine, CPU only (Accelerate), on the pinned 1.5B GGUF.
//   3. LlamaEngine (FALLBACK): llama.cpp b11960 universal xcframework + the pinned 1.5B GGUF.
// EngineSelector (PocketCore) picks one; ModelStore drives whichever is active.
//
// MLX: mlx-swift-lm (MLXLLM + MLXLMCommon) and swift-transformers (Tokenizers) are linked by
// project.yml. MLXEngine loads only Clarke Yoursa Tee's hash-pinned MLX 4-bit files
// (MLXModelPin.clarke1p5b4bit), only on a real device with Metal; in the Simulator it refuses and
// the next engine answers. Nothing here pretends MLX ran.

import Foundation
import Metal
#if canImport(MLXLLM) && canImport(Tokenizers)
import MLXLLM
import MLXLMCommon
import Tokenizers
#endif

protocol ChatEngine: Actor {
    nonisolated var kind: EngineKind { get }
    var isLoaded: Bool { get }
    func unload()
    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn]
    func begin(_ turns: [PromptTurn], maxTokens: Int) async throws -> Int
    func next() async throws -> String?
    func cancel()
}

extension LlamaEngine: ChatEngine {
    nonisolated var kind: EngineKind { .llamaCpp }
}

enum MLXEngineError: Error, CustomStringConvertible {
    case unavailable(String)
    var description: String {
        switch self { case .unavailable(let why): return "MLX unavailable: \(why)" }
    }
}

#if canImport(MLXLLM) && canImport(Tokenizers)
/// MLX Swift (mlx-swift-lm) on Clarke Yoursa Tee's own MLX 4-bit model (MLXModelPin), local
/// files only: nothing is downloaded by this engine. The tokenizer is swift-transformers
/// `AutoTokenizer` reading the pinned tokenizer.json / tokenizer_config.json / chat template.
actor MLXEngine: ChatEngine {
    nonisolated var kind: EngineKind { .mlx }
    nonisolated static let linked = true

    private var container: ModelContainer?
    private var stream: AsyncThrowingStream<String, Error>.AsyncIterator?

    var isLoaded: Bool { container != nil }

    func load(directory: URL) async throws -> String {
        // Never claim MLX where it cannot run (Simulator / no Metal) or on unverified files.
        if let why = EngineSelector.mlxBlocker(EngineDetector.environment()) {
            throw MLXEngineError.unavailable(why)
        }
        guard case .verified = MLXModelState.check(dir: directory, pin: MLXModelPin.selected) else {
            throw MLXEngineError.unavailable("MLX model files are missing or fail their SHA-256 pin")
        }
        container = try await loadModelContainer(from: directory, using: LocalTokenizerLoader())
        return "MLX Swift (primary) · \(MLXModelPin.selected?.label ?? directory.lastPathComponent)"
    }
    func unload() { stream = nil; container = nil }
    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn] {
        // Same system message as the other engines; ~4 chars/token estimate for the window.
        PromptWindow.fit(system: HiddenPrompt.compose(system), history: history, user: user,
                         budget: Int(RuntimePolicy.contextTokens) - RuntimePolicy.replyReserve,
                         tokenCount: { max(1, $0.utf8.count / 4) })
    }
    func begin(_ turns: [PromptTurn], maxTokens: Int) async throws -> Int {
        guard let container else { throw MLXEngineError.unavailable("not loaded") }
        guard let last = turns.last, last.role == "user" else { throw MLXEngineError.unavailable("no user turn") }
        let system = turns.first(where: { $0.role == "system" })?.content
        let history: [Chat.Message] = turns.dropLast().compactMap { t in
            switch t.role {
            case "user": return .user(t.content)
            case "assistant": return .assistant(t.content)
            default: return nil
            }
        }
        let session = ChatSession(container, instructions: system, history: history,
                                  generateParameters: GenerateParameters(maxTokens: maxTokens, temperature: 0.6))
        stream = session.streamResponse(to: last.content).makeAsyncIterator()
        let text = turns.map(\.content).joined(separator: "\n")
        return await container.perform { ctx in ctx.tokenizer.encode(text: text).count }
    }
    func next() async throws -> String? {
        guard var it = stream else { return nil }
        let piece = try await it.next()
        stream = piece == nil ? nil : it
        return piece
    }
    func cancel() { stream = nil }
}

/// MLXLMCommon.TokenizerLoader over swift-transformers, from the local model folder.
struct LocalTokenizerLoader: MLXLMCommon.TokenizerLoader {
    func load(from directory: URL) async throws -> any MLXLMCommon.Tokenizer {
        TokenizerBridge(try await Tokenizers.AutoTokenizer.from(modelFolder: directory))
    }
}

struct TokenizerBridge: MLXLMCommon.Tokenizer {
    let upstream: any Tokenizers.Tokenizer
    init(_ upstream: any Tokenizers.Tokenizer) { self.upstream = upstream }
    func encode(text: String, addSpecialTokens: Bool) -> [Int] { upstream.encode(text: text, addSpecialTokens: addSpecialTokens) }
    func decode(tokenIds: [Int], skipSpecialTokens: Bool) -> String { upstream.decode(tokens: tokenIds, skipSpecialTokens: skipSpecialTokens) }
    func convertTokenToId(_ token: String) -> Int? { upstream.convertTokenToId(token) }
    func convertIdToToken(_ id: Int) -> String? { upstream.convertIdToToken(id) }
    var bosToken: String? { upstream.bosToken }
    var eosToken: String? { upstream.eosToken }
    var unknownToken: String? { upstream.unknownToken }
    func applyChatTemplate(messages: [[String: any Sendable]], tools: [[String: any Sendable]]?,
                           additionalContext: [String: any Sendable]?) throws -> [Int] {
        do {
            return try upstream.applyChatTemplate(messages: messages, tools: tools, additionalContext: additionalContext)
        } catch Tokenizers.TokenizerError.missingChatTemplate {
            throw MLXLMCommon.TokenizerError.missingChatTemplate
        }
    }
}
#else
actor MLXEngine: ChatEngine {
    nonisolated var kind: EngineKind { .mlx }
    /// Flip to true in the same change that links the MLX Swift package and implements load/generate.
    nonisolated static let linked = false   // MLX Swift packages not in this build

    var isLoaded: Bool { false }

    func load(directory: URL) throws -> String {
        throw MLXEngineError.unavailable(EngineSelector.mlxBlocker(EngineDetector.environment()) ?? "MLX Swift is not linked into this build")
    }
    func unload() {}
    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn] {
        [PromptTurn(role: "system", content: system)] + history + [PromptTurn(role: "user", content: user)]
    }
    func begin(_ turns: [PromptTurn], maxTokens: Int) throws -> Int {
        throw MLXEngineError.unavailable("not loaded")
    }
    func next() throws -> String? { nil }
    func cancel() {}
}

#endif

/// ClarkeEngine as a ChatEngine. ClarkeEngine itself is a `struct` (like sovereign/PlanckEngine);
/// its streaming state lives in `ClarkeEngine.Session`, which this actor owns.
actor ClarkeChatEngine: ChatEngine {
    nonisolated var kind: EngineKind { .clarke }
    private var session: ClarkeEngine.Session?

    var isLoaded: Bool { session != nil }

    func load(path: String) throws -> String {
        let s = try ClarkeEngine.Session(modelPath: path, nCtx: ClarkeEngine.contextTokens)
        session = s
        let hp = s.model.hp
        return "\(ClarkeEngine.engineName) · \(hp.nLayer) layers · n_embd \(hp.nEmbd) · \(hp.nHead)/\(hp.nHeadKV) heads · ctx \(s.model.nCtx) · rope \(Int(hp.ropeBase))"
    }
    func unload() { session = nil }
    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn] {
        // Same system message as the llama.cpp path (HiddenPrompt + visible instructions).
        let sys = HiddenPrompt.compose(system)
        guard let s = session else { return [PromptTurn(role: "system", content: sys), PromptTurn(role: "user", content: user)] }
        return PromptWindow.fit(system: sys, history: history, user: user,
                                budget: s.model.nCtx - RuntimePolicy.replyReserve, tokenCount: { s.tokenCount($0) })
    }
    func begin(_ turns: [PromptTurn], maxTokens: Int) throws -> Int {
        guard let s = session else { throw GGUFError.open("ClarkeEngine not loaded") }
        return try s.begin(turns, maxTokens: maxTokens, temperature: ClarkeEngine.temperature,
                           seed: UInt64(Date().timeIntervalSince1970 * 1000))
    }
    func next() throws -> String? { try session?.next() }
    func cancel() { session?.cancel() }
}

/// Reads the real device/build facts for EngineSelector.
enum EngineDetector {
    static var isSimulator: Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }

    static func mlxModelDirectory() -> URL? {
        guard let pin = MLXModelPin.selected,
              let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
        else { return nil }
        return base.appendingPathComponent("Models/MLX").appendingPathComponent(pin.directoryName)
    }

    static func environment(ggufPath: String? = nil) -> EngineEnvironment {
        let model: MLXModelState
        if let dir = mlxModelDirectory() {
            model = MLXModelState.check(dir: dir, pin: MLXModelPin.selected)
        } else {
            model = .notPublished
        }
        return EngineEnvironment(isSimulator: isSimulator,
                                 hasMetal: MTLCreateSystemDefaultDevice() != nil,
                                 mlxLinked: MLXEngine.linked,
                                 mlxModel: model,
                                 clarkeModel: ClarkeModelState.check(path: ggufPath))
    }
}
