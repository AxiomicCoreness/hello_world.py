// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// SIMULATOR SCREENSHOTS ONLY. Never part of the real app.
//
// llama.cpp's b11960 xcframework ships ios-arm64 and macos slices but no iOS Simulator slice, so
// ios/ClarkePocket cannot link `llama` for the simulator. The ios-sim-screenshots workflow builds
// ClarkePocket from clarke-pocket-sim.yml, which leaves out ClarkePocket/LlamaEngine.swift and the
// LlamaBinary package and compiles this file instead. It has the same internal API as the real
// LlamaEngine (LlamaError, LoadedModelInfo, actor LlamaEngine), so every SwiftUI file compiles
// unchanged; it just never loads a model: `load` throws, and nothing generates.

import Foundation

typealias llama_token = Int32

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
        case .loadFailed(let p): return "simulator build: llama.cpp is not linked, cannot load \(p)"
        case .contextFailed: return "could not create a llama context"
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
    var templateSource: String
    var temperature: Float
    var topP: Float
}

actor LlamaEngine {
    var isLoaded: Bool { false }

    func load(path: String,
              contextTokens: Int32 = RuntimePolicy.contextTokens,
              gpuLayers: Int32 = RuntimePolicy.gpuLayers,
              threads: (gen: Int32, batch: Int32)) throws -> LoadedModelInfo {
        throw LlamaError.loadFailed(path)
    }

    func unload() {}

    func render(_ turns: [PromptTurn]) throws -> String { throw LlamaError.notLoaded }

    func tokenize(_ text: String) throws -> [llama_token] { throw LlamaError.notLoaded }

    func tokenCount(_ turns: [PromptTurn]) -> Int { Int.max }

    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn] {
        PromptWindow.fit(system: system, history: history, user: user,
                         budget: Int(RuntimePolicy.contextTokens) - RuntimePolicy.replyReserve) { tokenCount($0) }
    }

    func begin(_ turns: [PromptTurn], maxTokens: Int) throws -> Int { throw LlamaError.notLoaded }

    func next() throws -> String? { nil }

    func cancel() {}
}
