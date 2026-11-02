// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// HHMIJaneliaMap.xml (a placeholder) and the PC-side Ray/CUDA backend option (remote, off by
// default, loopback only). Offline: the remote is a stub; nothing here opens a socket.

import XCTest
@testable import PocketCore

final class ConnectomeAndRemoteTests: XCTestCase {
    private var iosRoot: URL {
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    }
    private var bundledCopy: URL { iosRoot.appendingPathComponent("ClarkePocket/Resources/HHMIJaneliaMap.xml") }
    private var repoOriginal: URL {
        iosRoot.deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("src/main/resources/HHMIJaneliaMap.xml")
    }

    func testBundledCopyIsByteIdenticalToTheRepoPlaceholder() throws {
        XCTAssertEqual(try Data(contentsOf: bundledCopy), try Data(contentsOf: repoOriginal))
    }

    func testPlaceholderIsCalledAPlaceholder() throws {
        let text = try String(contentsOf: bundledCopy, encoding: .utf8)
        XCTAssertTrue(text.contains("PLACEHOLDER"))
        XCTAssertTrue(Connectome.placeholderLabel.hasPrefix("HHMIJaneliaMap.xml (placeholder"))
        XCTAssertTrue(Connectome.placeholderLabel.contains("NOT HHMI Janelia FlyEM"))
        XCTAssertTrue(try Connectome.parse(Data(contentsOf: bundledCopy)).isPlaceholder)
    }

    func testParsesTheThreeNeuronRing() throws {
        let c = try Connectome.parse(Data(contentsOf: bundledCopy))
        XCTAssertEqual(c.neurons, ["A", "B", "C"])
        XCTAssertEqual(c.synapses, [Synapse(from: "A", to: "B", weight: 1.0),
                                    Synapse(from: "B", to: "C", weight: 0.8),
                                    Synapse(from: "C", to: "A", weight: 0.5)])
    }

    func testRejectsBrokenMaps() {
        let unknown = Data(#"<hemibrain><neuron id="A"/><connection from="A" to="Z" weight="1"/></hemibrain>"#.utf8)
        XCTAssertThrowsError(try Connectome.parse(unknown)) { XCTAssertEqual($0 as? ConnectomeError, .unknownNeuron("Z")) }
        let dup = Data(#"<hemibrain><neuron id="A"/><neuron id="A"/></hemibrain>"#.utf8)
        XCTAssertThrowsError(try Connectome.parse(dup)) { XCTAssertEqual($0 as? ConnectomeError, .duplicateNeuron("A")) }
        let weight = Data(#"<hemibrain><neuron id="A"/><connection from="A" to="A" weight="x"/></hemibrain>"#.utf8)
        XCTAssertThrowsError(try Connectome.parse(weight)) { XCTAssertEqual($0 as? ConnectomeError, .badWeight("x")) }
        XCTAssertThrowsError(try Connectome.parse(Data("<other/>".utf8)))
    }

    func testSimulationIsDeterministicAndLabelled() throws {
        let c = try Connectome.parse(Data(contentsOf: bundledCopy))
        let sim = ConnectomeSimulation()
        XCTAssertTrue(sim.isSimulation)
        XCTAssertTrue(ConnectomeSimulation.label.hasPrefix("Simulation"))
        let r = sim.run(c, stimulate: "A", steps: 5)
        // A fires, drives B (1.0 >= 0.75), B drives C (0.8), C -> A is only 0.5: the wave stops.
        XCTAssertEqual(r, [["A"], ["B"], ["C"], [], []])
        XCTAssertEqual(sim.run(c, stimulate: "A", steps: 5), r)
    }

    func testRayCUDAIsRemoteOnlyAndOffByDefault() {
        XCTAssertFalse(ComputeBackend.pcRayCUDA.runsOnDevice)
        XCTAssertTrue(ComputeBackend.onDevice.runsOnDevice)
        XCTAssertTrue(ComputeBackend.pcRayCUDA.label.contains("never on the iPhone"))
        XCTAssertFalse(RayCUDARemoteConfig().enabled)
        let d = UserDefaults(suiteName: "raycuda-\(UUID().uuidString)")!
        XCTAssertFalse(RayCUDARemoteConfig.load(d).enabled)
        XCTAssertEqual(RayCUDARemoteConfig.load(d).endpoint, "http://127.0.0.1:8095")
    }

    func testEndpointMustBeLoopback127() throws {
        XCTAssertEqual(try RayCUDARemoteConfig.healthURL(for: "http://127.0.0.1:8095").absoluteString,
                       "http://127.0.0.1:8095/healthz")
        XCTAssertThrowsError(try RayCUDARemoteConfig.healthURL(for: "http://0.0.0.0:8095")) {
            XCTAssertEqual($0 as? RemoteEndpointError, .notLoopback("0.0.0.0"))
        }
        XCTAssertThrowsError(try RayCUDARemoteConfig.healthURL(for: "http://192.168.1.5:8095"))
        XCTAssertThrowsError(try RayCUDARemoteConfig.healthURL(for: "http://localhost:8095"))
        XCTAssertThrowsError(try RayCUDARemoteConfig.healthURL(for: "https://127.0.0.1:8095")) {
            XCTAssertEqual($0 as? RemoteEndpointError, .notHTTP)
        }
        XCTAssertThrowsError(try RayCUDARemoteConfig.healthURL(for: "http://127.0.0.1")) {
            XCTAssertEqual($0 as? RemoteEndpointError, .badPort)
        }
    }

    func testHealthContractAndStubIsASimulation() async throws {
        let h = try RayCUDAHealth.decode(Data(#"{"backend":"ray-cuda","cuda_available":true,"ray_workers":4,"simulated":false}"#.utf8))
        XCTAssertEqual(h, RayCUDAHealth(backend: "ray-cuda", cudaAvailable: true, rayWorkers: 4, simulated: false))
        XCTAssertEqual(h.summary, "ray-cuda: CUDA available on the PC, 4 Ray workers")
        let stub = try await StubRayCUDARemote(workers: 1).health()
        XCTAssertTrue(stub.simulated)
        XCTAssertFalse(stub.cudaAvailable)
        XCTAssertTrue(stub.summary.contains("SIMULATION"))
    }
}
