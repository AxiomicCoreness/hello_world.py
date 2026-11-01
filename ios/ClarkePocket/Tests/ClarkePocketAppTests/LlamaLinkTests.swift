// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// App-hosted tests (run inside ClarkePocket.app on the iOS Simulator in CI). They exercise the
// real llama.framework slice that is linked into the app, without any model weights:
// model files are never committed, so the "model" here is a missing path or a small stub file.

import XCTest
@testable import ClarkePocket

final class LlamaLinkTests: XCTestCase {
    func testLlamaFrameworkRunsInThisProcess() {
        let info = LlamaEngine.systemInfo()
        XCTAssertFalse(info.isEmpty, "llama_print_system_info() returned nothing")
    }

    func testMissingModelPathFailsCleanly() async {
        let engine = LlamaEngine()
        let path = NSTemporaryDirectory() + "clarkepocket-missing-\(UUID().uuidString).gguf"
        do {
            _ = try await engine.load(path: path, contextTokens: 256, gpuLayers: 0, threads: (gen: 1, batch: 1))
            XCTFail("loading a missing file must throw")
        } catch LlamaError.loadFailed(let p) {
            XCTAssertEqual(p, path)
        } catch {
            XCTFail("unexpected error \(error)")
        }
        let loaded = await engine.isLoaded
        XCTAssertFalse(loaded)
    }

    func testStubGGUFFileIsRejectedCleanly() async throws {
        // A stub, not a model: GGUF magic + version 3 + zero tensors/kv, then garbage.
        var bytes: [UInt8] = Array("GGUF".utf8)
        bytes += [3, 0, 0, 0]
        bytes += [UInt8](repeating: 0, count: 16)
        bytes += [UInt8](repeating: 0xAB, count: 64)
        let url = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("clarkepocket-stub-\(UUID().uuidString).gguf")
        try Data(bytes).write(to: url)
        defer { try? FileManager.default.removeItem(at: url) }
        let engine = LlamaEngine()
        do {
            _ = try await engine.load(path: url.path, contextTokens: 256, gpuLayers: 0, threads: (gen: 1, batch: 1))
            XCTFail("a stub file with no tensors must not load as a model")
        } catch is LlamaError {
            // loadFailed or contextFailed: either way no crash and nothing stays loaded
        }
        let loaded = await engine.isLoaded
        XCTAssertFalse(loaded)
    }

    func testDefaultPinStaysOn1p5B() {
        XCTAssertEqual(ModelPin.selected, ModelPinSpec.deepseekR2_1p5b)
        XCTAssertEqual(ModelPin.fileName, "deepseek-r2-1.5b-Q4_K_M.gguf")
        XCTAssertEqual(ModelPin.sha256, "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1")
    }
}
