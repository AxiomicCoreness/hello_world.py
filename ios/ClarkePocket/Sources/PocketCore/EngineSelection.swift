// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Which on-device engine answers, in this order:
//   1. MLX Swift with Clarke Yoursa Tee's own MLX-converted model (PRIMARY);
//   2. ClarkeEngine, Clarke Yoursa Tee's own pure-Swift qwen2 engine on the pinned GGUF (CPU);
//   3. llama.cpp b11960 with the pinned GGUF (ModelPin, 1.5B) (FALLBACK).
// Each step is skipped automatically when it cannot run (MLX: Simulator, no Metal, not linked,
// model not published / missing / SHA-256 mismatch; ClarkeEngine: no GGUF on the phone or a GGUF
// it cannot read). Any engine can also be chosen in the Chat tab. Pure logic, tested offline
// (EngineSelectionTests).

import Foundation

public enum EngineKind: String, CaseIterable, Sendable {
    case mlx
    case clarke
    case llamaCpp

    public var label: String {
        switch self {
        case .mlx: return "MLX Swift (primary)"
        case .clarke: return "ClarkeEngine (Clarke Yoursa Tee's own, CPU)"
        case .llamaCpp: return "llama.cpp b11960 GGUF (fallback)"
        }
    }
    public var shortLabel: String {
        switch self {
        case .mlx: return "MLX"
        case .clarke: return "CLARKEENGINE"
        case .llamaCpp: return "LLAMA.CPP"
        }
    }
}

/// The user's setting (Chat tab). Stored under `key`; unset means `.automatic`.
public enum EnginePreference: String, CaseIterable, Sendable {
    case automatic
    case mlx
    case clarke
    case llamaCpp

    public static let key = "enginePreference"
    public var label: String {
        switch self {
        case .automatic: return "Automatic (MLX, then ClarkeEngine, then llama.cpp)"
        case .mlx: return "MLX Swift"
        case .clarke: return "ClarkeEngine (pure Swift, CPU)"
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

/// Can ClarkeEngine run the GGUF on this phone?
public enum ClarkeModelState: Equatable, Sendable {
    case noFile
    case unreadable(String)   // GGUF header / architecture / tensor types it cannot handle
    case ready

    /// Cheap check: parse the GGUF header and tensor index (mmap; no weights are read).
    public static func check(path: String?) -> ClarkeModelState {
        guard let path, FileManager.default.fileExists(atPath: path) else { return .noFile }
        do {
            let g = try GGUFFile(path: path)
            let arch = g.string("general.architecture") ?? "?"
            guard arch == "qwen2" else { return .unreadable("architecture \(arch) is not qwen2") }
            for name in g.tensorOrder { _ = try g.tensor(name) }
            return .ready
        } catch {
            return .unreadable("\(error)")
        }
    }
}

/// What the device and this build can do.
public struct EngineEnvironment: Equatable, Sendable {
    public var isSimulator: Bool
    public var hasMetal: Bool
    public var mlxLinked: Bool
    public var mlxModel: MLXModelState
    public var clarkeModel: ClarkeModelState
    public init(isSimulator: Bool, hasMetal: Bool, mlxLinked: Bool, mlxModel: MLXModelState,
                clarkeModel: ClarkeModelState = .noFile) {
        self.isSimulator = isSimulator
        self.hasMetal = hasMetal
        self.mlxLinked = mlxLinked
        self.mlxModel = mlxModel
        self.clarkeModel = clarkeModel
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

    /// nil when ClarkeEngine can run; else the reason it cannot.
    public static func clarkeBlocker(_ env: EngineEnvironment) -> String? {
        switch env.clarkeModel {
        case .noFile: return "no GGUF model file on this device"
        case .unreadable(let why): return "cannot read the GGUF (\(why))"
        case .ready: return nil
        }
    }

    public static func choose(_ pref: EnginePreference, _ env: EngineEnvironment) -> EngineChoice {
        switch pref {
        case .llamaCpp:
            return EngineChoice(active: .llamaCpp, isFallback: true, reason: "llama.cpp chosen in settings")
        case .clarke:
            if let why = clarkeBlocker(env) {
                return EngineChoice(active: .llamaCpp, isFallback: true, reason: "ClarkeEngine chosen but unavailable: " + why)
            }
            return EngineChoice(active: .clarke, isFallback: false, reason: "ClarkeEngine chosen in settings")
        case .mlx, .automatic:
            guard let mlxWhy = mlxBlocker(env) else {
                return EngineChoice(active: .mlx, isFallback: false, reason: "MLX model verified")
            }
            let prefix = pref == .mlx ? "MLX chosen but unavailable: " : "MLX: "
            if pref == .automatic, clarkeBlocker(env) == nil {
                return EngineChoice(active: .clarke, isFallback: false, reason: prefix + mlxWhy)
            }
            let clarkeWhy = pref == .automatic ? "; ClarkeEngine: " + (clarkeBlocker(env) ?? "") : ""
            return EngineChoice(active: .llamaCpp, isFallback: true, reason: prefix + mlxWhy + clarkeWhy)
        }
    }

    /// After an engine failed at load time (e.g. out of memory): the next one in the order.
    public static func afterLoadFailure(of kind: EngineKind, _ error: String, _ env: EngineEnvironment) -> EngineChoice {
        if kind == .mlx, clarkeBlocker(env) == nil {
            return EngineChoice(active: .clarke, isFallback: false, reason: "MLX failed to load (\(error)); using ClarkeEngine")
        }
        let name = kind == .mlx ? "MLX" : "ClarkeEngine"
        return EngineChoice(active: .llamaCpp, isFallback: true, reason: "\(name) failed to load (\(error)); using llama.cpp")
    }
}
