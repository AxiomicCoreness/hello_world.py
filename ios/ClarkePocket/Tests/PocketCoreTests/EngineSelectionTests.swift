// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// MLX primary / llama.cpp fallback selection, offline. Model files here are tiny temp stubs.

import XCTest
@testable import PocketCore

final class EngineSelectionTests: XCTestCase {
    private func env(sim: Bool = false, metal: Bool = true, linked: Bool = true,
                     model: MLXModelState = .verified) -> EngineEnvironment {
        EngineEnvironment(isSimulator: sim, hasMetal: metal, mlxLinked: linked, mlxModel: model)
    }

    func testMLXIsPrimaryWhenEverythingIsThere() {
        let c = EngineSelector.choose(.automatic, env())
        XCTAssertEqual(c.active, .mlx)
        XCTAssertFalse(c.isFallback)
    }

    func testFallsBackToLlamaWhenMLXCannotRun() {
        let cases: [(EngineEnvironment, String)] = [
            (env(sim: true), "Simulator"),
            (env(metal: false), "Metal"),
            (env(linked: false), "not linked"),
            (env(model: .notPublished), "published"),
            (env(model: .missing("model.safetensors")), "model.safetensors"),
            (env(model: .shaMismatch("config.json")), "SHA-256"),
        ]
        for (e, word) in cases {
            let c = EngineSelector.choose(.automatic, e)
            XCTAssertEqual(c.active, .llamaCpp, "\(e)")
            XCTAssertTrue(c.isFallback)
            XCTAssertTrue(c.reason.contains(word), c.reason)
        }
    }

    func testSettingForcesLlamaAndExplainsAForcedMLX() {
        XCTAssertEqual(EngineSelector.choose(.llamaCpp, env()).active, .llamaCpp)
        let c = EngineSelector.choose(.mlx, env(sim: true))
        XCTAssertEqual(c.active, .llamaCpp)
        XCTAssertTrue(c.reason.hasPrefix("MLX chosen but unavailable"))
        XCTAssertEqual(EngineSelector.choose(.mlx, env()).active, .mlx)
        XCTAssertEqual(EngineSelector.afterMLXLoadFailure("oom").active, .llamaCpp)
    }

    func testPreferenceDefaultsToAutomatic() {
        let d = UserDefaults(suiteName: "engine-\(UUID().uuidString)")!
        XCTAssertEqual(EnginePreference.load(d), .automatic)
        d.set("llamaCpp", forKey: EnginePreference.key)
        XCTAssertEqual(EnginePreference.load(d), .llamaCpp)
        d.set("bogus", forKey: EnginePreference.key)
        XCTAssertEqual(EnginePreference.load(d), .automatic)
    }

    func testNoMLXModelPublishedYetAndGGUFFallbackStays1p5B() {
        XCTAssertNil(MLXModelPin.selected)
        XCTAssertEqual(MLXModelState.check(dir: FileManager.default.temporaryDirectory, pin: MLXModelPin.selected), .notPublished)
        XCTAssertEqual(ModelPin.selected, ModelPinSpec.deepseekR2_1p5b)
    }

    func testMLXFileCheckMissingMismatchVerified() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("mlx-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        let body = Data("{\"stub\":true}".utf8)
        let f = dir.appendingPathComponent("config.json")
        try body.write(to: f)
        let good = try FileVerifier.sha256Hex(of: f)
        let pin = { (sha: String, size: Int64) in
            MLXModelPinSpec(releaseTag: "test", directoryName: "t",
                            files: [MLXModelFile(name: "config.json", sizeBytes: size, sha256: sha),
                                    MLXModelFile(name: "model.safetensors", sizeBytes: 1, sha256: String(repeating: "0", count: 64))],
                            label: "stub")
        }
        XCTAssertEqual(MLXModelState.check(dir: dir, pin: pin(good, Int64(body.count))), .missing("model.safetensors"))
        XCTAssertEqual(MLXModelState.check(dir: dir, pin: pin(String(repeating: "f", count: 64), Int64(body.count))), .shaMismatch("config.json"))
        XCTAssertEqual(MLXModelState.check(dir: dir, pin: pin(good, 999)), .shaMismatch("config.json"))
        let one = MLXModelPinSpec(releaseTag: "test", directoryName: "t",
                                  files: [MLXModelFile(name: "config.json", sizeBytes: Int64(body.count), sha256: good)], label: "stub")
        XCTAssertEqual(MLXModelState.check(dir: dir, pin: one), .verified)
    }
}
