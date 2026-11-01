// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Where an answer can be computed. iOS has no CUDA, so CUDA never runs on the iPhone: the
// Ray/CUDA option is a REMOTE, PC-side backend, reached only at an http://127.0.0.1:<port>
// endpoint (the PC's loopback, e.g. from the Simulator on that Mac, or through a forwarded port).
// OFF by default. This repo does not (yet) contain a PC-side Ray/CUDA service that answers this
// contract; the client is tested offline against a stub, and Chat never routes to it.

import Foundation

public enum ComputeBackend: String, CaseIterable, Sendable {
    case onDevice
    case pcBotIRC
    case pcRayCUDA

    public var label: String {
        switch self {
        case .onDevice: return "On this iPhone (llama.cpp, Metal)"
        case .pcBotIRC: return "PC bot over IRC (opt-in fallback, IRC tab)"
        case .pcRayCUDA: return "PC-side Ray/CUDA (remote: runs on your PC, never on the iPhone)"
        }
    }

    /// Only the on-device model runs on the phone.
    public var runsOnDevice: Bool { self == .onDevice }
}

public enum RemoteEndpointError: Error, Equatable, CustomStringConvertible {
    case notHTTP
    case notLoopback(String)
    case badPort

    public var description: String {
        switch self {
        case .notHTTP: return "endpoint must be http://127.0.0.1:<port>"
        case .notLoopback(let h): return "endpoint host must be 127.0.0.1, not \(h)"
        case .badPort: return "endpoint needs a port 1-65535"
        }
    }
}

/// Settings for the PC-side Ray/CUDA backend. Disabled unless the user switches it on.
public struct RayCUDARemoteConfig: Equatable, Sendable {
    public static let enabledKey = "rayCudaRemoteEnabled"
    public static let endpointKey = "rayCudaRemoteEndpoint"
    public static let defaultEndpoint = "http://127.0.0.1:8095"

    public var enabled: Bool
    public var endpoint: String

    public init(enabled: Bool = false, endpoint: String = RayCUDARemoteConfig.defaultEndpoint) {
        self.enabled = enabled
        self.endpoint = endpoint
    }

    public static func load(_ d: UserDefaults) -> RayCUDARemoteConfig {
        RayCUDARemoteConfig(enabled: d.bool(forKey: enabledKey),
                            endpoint: d.string(forKey: endpointKey) ?? defaultEndpoint)
    }

    /// Loopback only: http, host exactly 127.0.0.1, explicit port. Returns the health URL.
    public static func healthURL(for endpoint: String) throws -> URL {
        guard let c = URLComponents(string: endpoint), c.scheme == "http" else { throw RemoteEndpointError.notHTTP }
        guard c.host == "127.0.0.1" else { throw RemoteEndpointError.notLoopback(c.host ?? "") }
        guard let port = c.port, (1...65535).contains(port) else { throw RemoteEndpointError.badPort }
        var h = URLComponents()
        h.scheme = "http"
        h.host = "127.0.0.1"
        h.port = port
        h.path = "/healthz"
        return h.url!
    }
}

/// What the PC-side service reports at GET /healthz (the contract this client expects).
public struct RayCUDAHealth: Codable, Equatable, Sendable {
    public let backend: String          // "ray-cuda"
    public let cudaAvailable: Bool
    public let rayWorkers: Int
    /// True when the PC side answered from a stub/simulation rather than real CUDA kernels.
    public let simulated: Bool

    enum CodingKeys: String, CodingKey {
        case backend
        case cudaAvailable = "cuda_available"
        case rayWorkers = "ray_workers"
        case simulated
    }

    public init(backend: String, cudaAvailable: Bool, rayWorkers: Int, simulated: Bool) {
        self.backend = backend
        self.cudaAvailable = cudaAvailable
        self.rayWorkers = rayWorkers
        self.simulated = simulated
    }

    public static func decode(_ data: Data) throws -> RayCUDAHealth {
        try JSONDecoder().decode(RayCUDAHealth.self, from: data)
    }

    /// One line for the UI. A simulated answer is always called a simulation.
    public var summary: String {
        let kind = simulated ? "SIMULATION (no real CUDA)" : (cudaAvailable ? "CUDA available on the PC" : "no CUDA on the PC")
        return "\(backend): \(kind), \(rayWorkers) Ray worker\(rayWorkers == 1 ? "" : "s")"
    }
}

/// Anything that can answer the health probe: the real loopback HTTP client in the app, or a stub.
public protocol RayCUDARemote: Sendable {
    func health() async throws -> RayCUDAHealth
}

/// Offline stand-in for tests and previews. Always reports itself as simulated.
public struct StubRayCUDARemote: RayCUDARemote {
    public let workers: Int
    public init(workers: Int = 0) { self.workers = workers }
    public func health() async throws -> RayCUDAHealth {
        RayCUDAHealth(backend: "ray-cuda-stub", cudaAvailable: false, rayWorkers: workers, simulated: true)
    }
}
