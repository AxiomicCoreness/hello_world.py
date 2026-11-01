// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Which on-device engine answers: MLX Swift with Clarke Yoursa Tee's own MLX-converted model is
// the PRIMARY engine; llama.cpp b11960 with the pinned GGUF (ModelPin, 1.5B) is the FALLBACK.
// The fallback is chosen automatically whenever MLX cannot run (Simulator, no Metal, MLX not
// linked into this build, MLX model not published / not on the phone / SHA-256 mismatch) and
// can also be forced in the Chat tab. Pure logic, tested offline (EngineSelectionTests).

import Foundation

public enum EngineKind: String, CaseIterable, Sendable {
    case mlx
    case llamaCpp

    public var label: String {
        switch self {
        case .mlx: return "MLX Swift (primary)"
        case .llamaCpp: return "llama.cpp b11960 GGUF (fallback)"
        }
    }
    public var shortLabel: String { self == .mlx ? "MLX" : "LLAMA.CPP" }
}

/// The user's setting (Chat tab). Stored under `key`; unset means `.automatic`.
public enum EnginePreference: String, CaseIterable, Sendable {
    case automatic
    case mlx
    case llamaCpp

    public static let key = "enginePreference"
    public var label: String {
        switch self {
        case .automatic: return "Automatic (MLX, else llama.cpp)"
        case .mlx: return "MLX Swift"
        case .llamaCpp: return "llama.cpp (GGUF)"
        }
    }
    public static func load(_ d: UserDefaults) -> EnginePreference {
        d.string(forKey: key).flatMap(EnginePreference.init(rawValue:)) ?? .automatic
    }
}

/// One file of an MLX-converted model directory, pinned by size and SHA-256.
public struct MLXModelFile: Equatable, Sendable {
    public let name: String
    public let sizeBytes: Int64
    public let sha256: String
    public init(name: String, sizeBytes: Int64, sha256: String) {
        self.name = name
        self.sizeBytes = sizeBytes
        self.sha256 = sha256
    }
}

/// Clarke Yoursa Tee's MLX-converted model: a GitHub release of this repo, one directory of files.
public struct MLXModelPinSpec: Equatable, Sendable {
    public let releaseTag: String
    public let directoryName: String
    public let files: [MLXModelFile]
    public let label: String
    public init(releaseTag: String, directoryName: String, files: [MLXModelFile], label: String) {
        self.releaseTag = releaseTag
        self.directoryName = directoryName
        self.files = files
        self.label = label
    }
}

public enum MLXModelPin {
    /// nil until an MLX-converted model of Clarke Yoursa Tee's own is published as a release of
    /// this repo with per-file SHA-256s. Until then the app always runs the llama.cpp fallback.
    public static let selected: MLXModelPinSpec? = nil
}

/// State of the MLX model files on the phone.
public enum MLXModelState: Equatable, Sendable {
    case notPublished
    case missing(String)        // first missing file
    case shaMismatch(String)    // first file whose size or SHA-256 differs
    case verified

    /// Check `dir` against `pin` (size first, then streaming SHA-256).
    public static func check(dir: URL, pin: MLXModelPinSpec?) -> MLXModelState {
        guard let pin else { return .notPublished }
        for f in pin.files {
            let url = dir.appendingPathComponent(f.name)
            guard let size = FileVerifier.fileSize(url) else { return .missing(f.name) }
            if size != f.sizeBytes { return .shaMismatch(f.name) }
            guard let hex = try? FileVerifier.sha256Hex(of: url), hex == f.sha256 else { return .shaMismatch(f.name) }
        }
        return .verified
    }
}

/// What the device and this build can do.
public struct EngineEnvironment: Equatable, Sendable {
    public var isSimulator: Bool
    public var hasMetal: Bool
    public var mlxLinked: Bool
    public var mlxModel: MLXModelState
    public init(isSimulator: Bool, hasMetal: Bool, mlxLinked: Bool, mlxModel: MLXModelState) {
        self.isSimulator = isSimulator
        self.hasMetal = hasMetal
        self.mlxLinked = mlxLinked
        self.mlxModel = mlxModel
    }
}

public struct EngineChoice: Equatable, Sendable {
    public let active: EngineKind
    public let isFallback: Bool
    /// Why this engine (shown under the Chat header).
    public let reason: String
}

public enum EngineSelector {
    /// nil when MLX can run; else the reason it cannot.
    public static func mlxBlocker(_ env: EngineEnvironment) -> String? {
        if env.isSimulator { return "MLX does not run in the iOS Simulator" }
        if !env.hasMetal { return "no Metal GPU" }
        if !env.mlxLinked { return "MLX Swift is not linked into this build" }
        switch env.mlxModel {
        case .notPublished: return "no MLX-converted model is published yet"
        case .missing(let f): return "MLX model file \(f) is not on this iPhone"
        case .shaMismatch(let f): return "MLX model file \(f) failed its SHA-256 check"
        case .verified: return nil
        }
    }

    public static func choose(_ pref: EnginePreference, _ env: EngineEnvironment) -> EngineChoice {
        if pref == .llamaCpp {
            return EngineChoice(active: .llamaCpp, isFallback: true, reason: "llama.cpp chosen in settings")
        }
        if let why = mlxBlocker(env) {
            let prefix = pref == .mlx ? "MLX chosen but unavailable: " : ""
            return EngineChoice(active: .llamaCpp, isFallback: true, reason: prefix + why)
        }
        return EngineChoice(active: .mlx, isFallback: false, reason: "MLX model verified")
    }

    /// After MLX failed at load time (e.g. out of memory): always the llama.cpp fallback.
    public static func afterMLXLoadFailure(_ error: String) -> EngineChoice {
        EngineChoice(active: .llamaCpp, isFallback: true, reason: "MLX failed to load (\(error)); using llama.cpp")
    }
}
