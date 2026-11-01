// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// One protocol for the two on-device engines:
//   * MLXEngine  (PRIMARY): MLX Swift + Clarke Yoursa Tee's own MLX-converted model (MLXModelPin).
//   * LlamaEngine (FALLBACK): llama.cpp b11960 universal xcframework + the pinned 1.5B GGUF.
// EngineSelector (PocketCore) picks one; ModelStore drives whichever is active.
//
// MLX status in this build: the MLX Swift package is NOT linked yet and no MLX-converted model is
// published (MLXModelPin.selected == nil), so MLXEngine.load always throws `.unavailable` and the
// llama.cpp fallback answers. Nothing here pretends MLX ran.

import Foundation
import Metal

protocol ChatEngine: Actor {
    nonisolated var kind: EngineKind { get }
    var isLoaded: Bool { get }
    func unload()
    func fitPrompt(system: String, history: [PromptTurn], user: String) -> [PromptTurn]
    func begin(_ turns: [PromptTurn], maxTokens: Int) throws -> Int
    func next() throws -> String?
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

actor MLXEngine: ChatEngine {
    nonisolated var kind: EngineKind { .mlx }
    /// Flip to true in the same change that links the MLX Swift package and implements load/generate.
    nonisolated static let linked = false

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

    static func environment() -> EngineEnvironment {
        let model: MLXModelState
        if let dir = mlxModelDirectory() {
            model = MLXModelState.check(dir: dir, pin: MLXModelPin.selected)
        } else {
            model = .notPublished
        }
        return EngineEnvironment(isSimulator: isSimulator,
                                 hasMetal: MTLCreateSystemDefaultDevice() != nil,
                                 mlxLinked: MLXEngine.linked,
                                 mlxModel: model)
    }
}
