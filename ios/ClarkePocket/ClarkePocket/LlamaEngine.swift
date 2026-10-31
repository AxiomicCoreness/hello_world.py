// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Thin Swift wrapper over llama.cpp's C API (module `llama`, pinned b11960 — see
// LlamaBinary/Package.swift). Modelled on llama.cpp's own examples/llama.swiftui
// (llama.cpp.swift/LibLlama.swift at b11960), with what a chat app needs on top:
//   * the chat template from the GGUF (`tokenizer.chat_template`, rendered by
//     llama_chat_apply_template; the built-in renderer recognises this model's DeepSeek-R1 template),
//   * BOS prepended when the template prints bos_token but the vocab won't add it,
//   * sampling from the GGUF's general.sampling.* hints (temp 0.6 / top_p 0.95 for this model),
//   * streaming pieces as complete UTF-8, a hard stop at the context edge, and cancellation
//     between tokens (the caller simply stops asking for the next piece).
// Everything runs on this actor; the UI never touches a llama pointer. Nothing here exits.

import Foundation
import llama

enum LlamaError: Error, CustomStringConvertible {
    case notLoaded
    case loadFailed(String)
    case contextFailed
    case templateFailed
    case tokenizeFailed
    case promptTooLong(tokens: Int, limit: Int)
    case decodeFailed(Int32)

    var description: String {
        switch self {
        case .notLoaded: return "no model loaded"
        case .loadFailed(let p): return "could not load model at \(p)"
        case .contextFailed: return "could not create a llama context (not enough memory?)"
        case .templateFailed: return "could not apply the chat template"
        case .tokenizeFailed: return "tokenizer failed"
        case let .promptTooLong(t, l): return "prompt is \(t) tokens; the context holds \(l)"
        case .decodeFailed(let c): return "llama_decode failed (\(c))"
        }
    }
}

struct LoadedModelInfo: Sendable {
    var description: String
    var contextTokens: Int32
    var threads: (gen: Int32, batch: Int32)
    var gpuLayers: Int32
    var templateSource: String   // "gguf" or "chatml (fallback)"
    var temperature: Float
    var topP: Float
}

actor LlamaEngine {
    private var model: OpaquePointer?
    private var ctx: OpaquePointer?
    private var vocab: OpaquePointer?
    private var sampler: UnsafeMutablePointer<llama_sampler>?
    private var template: String?
    private var templateIsFallback = false

    // Per-generation state
    private var nPast: Int32 = 0
    private var remaining = 0
    private var utf8 = UTF8Assembler()
    private var finished = true

    /// llama_backend_init once per process; never freed (the process may load/unload many times).
    private static let backend: Void = { llama_backend_init() }()

    var isLoaded: Bool { ctx != nil }

    func load(path: String,
              contextTokens: Int32 = RuntimePolicy.contextTokens,
              gpuLayers: Int32 = RuntimePolicy.gpuLayers,
              threads: (gen: Int32, batch: Int32)) throws -> LoadedModelInfo {
        unload()
        _ = Self.backend

        var mparams = llama_model_default_params()
        mparams.n_gpu_layers = gpuLayers      // Metal: all layers
        mparams.load_mode = LLAMA_LOAD_MODE_MMAP   // weights stay file-backed; iOS can page them (no mlock)
        guard let m = llama_model_load_from_file(path, mparams) else { throw LlamaError.loadFailed(path) }

        var cparams = llama_context_default_params()
        cparams.n_ctx = UInt32(contextTokens)
        cparams.n_batch = 512
        cparams.n_ubatch = 512
        cparams.n_threads = threads.gen
        cparams.n_threads_batch = threads.batch
        guard let c = llama_init_from_model(m, cparams) else {
            llama_model_free(m)
            throw LlamaError.contextFailed
        }
        model = m
        ctx = c
        vocab = llama_model_get_vocab(m)

        if let t = llama_model_chat_template(m, nil) {
            template = String(cString: t)
            templateIsFallback = false
        } else {
            template = "chatml"   // llama.cpp built-in name
            templateIsFallback = true
        }

        let temp = metaFloat("general.sampling.temp") ?? 0.6
        let topP = metaFloat("general.sampling.top_p") ?? 0.95
        let chain = llama_sampler_chain_init(llama_sampler_chain_default_params())!
        llama_sampler_chain_add(chain, llama_sampler_init_top_k(40))
        llama_sampler_chain_add(chain, llama_sampler_init_top_p(topP, 1))
        llama_sampler_chain_add(chain, llama_sampler_init_min_p(0.05, 1))
        llama_sampler_chain_add(chain, llama_sampler_init_temp(temp))
        llama_sampler_chain_add(chain, llama_sampler_init_dist(UInt32.random(in: 1...UInt32.max)))
        sampler = chain

        var desc = [CChar](repeating: 0, count: 256)
        let n = llama_model_desc(m, &desc, desc.count)
        let d = n > 0 ? String(cString: desc) : "model"
        return LoadedModelInfo(description: d, contextTokens: Int32(llama_n_ctx(c)), threads: threads,
                               gpuLayers: gpuLayers, templateSource: templateIsFallback ? "chatml (fallback)" : "gguf",
                               temperature: temp, topP: topP)
    }

    /// Free everything. Safe to call twice. (llama_backend_free is never called: see `backend`.)
    func unload() {
        finished = true
        if let s = sampler { llama_sampler_free(s) }
        if let c = ctx { llama_free(c) }
        if let m = model { llama_model_free(m) }
        sampler = nil; ctx = nil; model = nil; vocab = nil; template = nil
    }

    private func metaFloat(_ key: String) -> Float? {
        guard let m = model else { return nil }
        var buf = [CChar](repeating: 0, count: 64)
        guard llama_model_meta_val_str(m, key, &buf, buf.count) > 0 else { return nil }
        return Float(String(cString: buf))
    }

    // MARK: Prompt

    /// The chat rendered with the GGUF template, ending with the assistant cue.
    func render(_ turns: [PromptTurn]) throws -> String {
        guard let tmpl = template else { throw LlamaError.notLoaded }
        // C strings must stay alive during the call.
        let roles = turns.map { strdup($0.role) }
        let contents = turns.map { strdup($0.content) }
        defer { roles.forEach { free($0) }; contents.forEach { free($0) } }
        var msgs = zip(roles, contents).map { llama_chat_message(role: $0, content: $1) }
        let total = turns.reduce(0) { $0 + $1.content.utf8.count + 64 }
        var buf = [CChar](repeating: 0, count: max(1024, total * 2))
        var n = llama_chat_apply_template(tmpl, &msgs, msgs.count, true, &buf, Int32(buf.count))
        if n > Int32(buf.count) {
            buf = [CChar](repeating: 0, count: Int(n) + 1)
            n = llama_chat_apply_template(tmpl, &msgs, msgs.count, true, &buf, Int32(buf.count))
        }
        guard n >= 0 else { throw LlamaError.templateFailed }
        return String(decoding: buf.prefix(Int(n)).map { UInt8(bitPattern: $0) }, as: UTF8.self)
    }

    func tokenize(_ text: String) throws -> [llama_token] {
        guard let v = vocab else { throw LlamaError.notLoaded }
        let addSpecial = llama_vocab_get_add_bos(v)
        let len = Int32(text.utf8.count)
        var toks = [llama_token](repeating: 0, count: Int(len) + 8)
        var n = llama_tokenize(v, text, len, &toks, Int32(toks.count), addSpecial, true)
        if n < 0 {
            toks = [llama_token](repeating: 0, count: Int(-n))
            n = llama_tokenize(v, text, len, &toks, Int32(toks.count), addSpecial, true)
        }
        guard n >= 0 else { throw LlamaError.tokenizeFailed }
        var out = Array(toks.prefix(Int(n)))
        let bos = llama_vocab_bos(v)
        let startsWithBOS = out.first == bos
        if bos >= 0, RuntimePolicy.shouldPrependBOS(template: templateIsFallback ? nil : template,
                                                    vocabAddsBOS: addSpecial,
                                                    promptStartsWithBOS: startsWithBOS) {
            out.insert(bos, at: 0)
        }
        return out
    }

    /// Token count of the rendered chat (used to fit history into the context).
    func tokenCount(_ turns: [PromptTurn]) -> Int {
        guard let text = try? render(turns), let t = try? tokenize(text) else { return Int.max }
        return t.count
    }

    /// System + the newest history that fits + the new user message, measured with the real
    /// tokenizer and leaving `RuntimePolicy.replyReserve` tokens for the answer.
    /// The hidden system prompt (HiddenPrompt.swift) is prepended here, for every request (Chat
    /// and the IRC !llm responder); it never leaves this actor except into llama.cpp.
    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn] {
        let nCtx = ctx.map { Int(llama_n_ctx($0)) } ?? Int(RuntimePolicy.contextTokens)
        return PromptWindow.fit(system: HiddenPrompt.compose(system), history: history, user: user,
                                budget: nCtx - RuntimePolicy.replyReserve) { tokenCount($0) }
    }

    /// Prefill the prompt. Returns the prompt's token count. Then call `next()` until nil.
    func begin(_ turns: [PromptTurn], maxTokens: Int) throws -> Int {
        guard let c = ctx, let s = sampler else { throw LlamaError.notLoaded }
        let tokens = try tokenize(try render(turns))
        let nCtx = Int(llama_n_ctx(c))
        guard tokens.count < nCtx - 16 else { throw LlamaError.promptTooLong(tokens: tokens.count, limit: nCtx) }

        llama_memory_clear(llama_get_memory(c), true)
        llama_sampler_reset(s)
        utf8 = UTF8Assembler()
        let step = Int(llama_n_batch(c))
        var i = 0
        var buf = tokens
        while i < buf.count {
            let n = min(step, buf.count - i)
            let rc = buf.withUnsafeMutableBufferPointer { p in
                llama_decode(c, llama_batch_get_one(p.baseAddress! + i, Int32(n)))
            }
            guard rc == 0 else { finished = true; throw LlamaError.decodeFailed(rc) }
            i += n
        }
        nPast = Int32(tokens.count)
        remaining = min(maxTokens, nCtx - tokens.count - 1)
        finished = false
        return tokens.count
    }

    /// The next piece of text ("" while a multi-byte character is incomplete), or nil when done.
    func next() throws -> String? {
        guard !finished, let c = ctx, let s = sampler, let v = vocab else { return nil }
        if remaining <= 0 { finished = true; return utf8.flush() }
        var tok = llama_sampler_sample(s, c, -1)   // samples from the last logits and accepts it
        if llama_vocab_is_eog(v, tok) { finished = true; return utf8.flush() }
        let text = utf8.push(piece(tok))
        let rc = llama_decode(c, llama_batch_get_one(&tok, 1))
        guard rc == 0 else { finished = true; throw LlamaError.decodeFailed(rc) }
        nPast += 1
        remaining -= 1
        return text
    }

    /// Stop the current generation (the next `next()` returns nil).
    func cancel() { finished = true }

    /// Raw bytes of one token. `special: true` so <think> / </think> come through as text.
    private func piece(_ tok: llama_token) -> [UInt8] {
        guard let v = vocab else { return [] }
        var buf = [CChar](repeating: 0, count: 32)
        var n = llama_token_to_piece(v, tok, &buf, Int32(buf.count), 0, true)
        if n < 0 {
            buf = [CChar](repeating: 0, count: Int(-n))
            n = llama_token_to_piece(v, tok, &buf, Int32(buf.count), 0, true)
        }
        return n > 0 ? buf.prefix(Int(n)).map { UInt8(bitPattern: $0) } : []
    }
}
