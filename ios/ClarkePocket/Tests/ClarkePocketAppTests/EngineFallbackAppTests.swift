// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// App-side engine fallback, offline: in the Simulator the detector reports the Simulator, MLX
// refuses to load, and the selector hands the turn to the llama.cpp fallback.

import XCTest
@testable import ClarkePocket

final class EngineFallbackAppTests: XCTestCase {
    func testSimulatorSelectsLlamaFallback() {
        let env = EngineDetector.environment()
        XCTAssertTrue(env.isSimulator)
        // MLX Swift is linked into this build, but must never be selected in the Simulator.
        XCTAssertTrue(env.mlxLinked)
        XCTAssertEqual(EngineSelector.mlxBlocker(env), "MLX does not run in the iOS Simulator")
        XCTAssertEqual(env.clarkeModel, .noFile)   // fresh Simulator: no GGUF downloaded
        let c = EngineSelector.choose(.automatic, env)
        XCTAssertEqual(c.active, .llamaCpp)
        XCTAssertNotEqual(c.active, .mlx)
        XCTAssertTrue(c.isFallback)
    }

    func testClarkeEngineIsSelectedInTheSimulatorWhenAGGUFIsReadable() {
        var env = EngineDetector.environment()
        env.clarkeModel = .ready
        XCTAssertEqual(EngineSelector.choose(.automatic, env).active, .clarke)
    }

    func testClarkeChatEngineConformsAndFailsCleanlyWithoutAFile() async {
        let e = ClarkeChatEngine()
        XCTAssertEqual(e.kind, .clarke)
        do {
            _ = try await e.load(path: "/nonexistent/model.gguf")
            XCTFail("loaded a missing file")
        } catch {}
        let loaded = await e.isLoaded
        XCTAssertFalse(loaded)
    }

    func testMLXEngineRefusesHonestlyAndBothConform() async {
        let engines: [any ChatEngine] = [MLXEngine(), ClarkeChatEngine(), LlamaEngine()]
        XCTAssertEqual(engines.map { $0.kind }, [.mlx, .clarke, .llamaCpp])
        do {
            _ = try await MLXEngine().load(directory: FileManager.default.temporaryDirectory)
            XCTFail("MLX must not claim to load in the Simulator")
        } catch let e as MLXEngineError {
            XCTAssertTrue("\(e)".hasPrefix("MLX unavailable"))
        } catch {
            XCTFail("unexpected \(error)")
        }
    }
}
