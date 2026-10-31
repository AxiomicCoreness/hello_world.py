// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The pinned on-device model (selectable in code; 1.5B by default) and a streaming SHA-256 file verifier.
// The app (iOS) hashes with CryptoKit. Linux has no CryptoKit, so there — only for `swift test` —
// the same calls go to the small pure-Swift `SHA256` in SHA256Fallback.swift (same API subset).

import Foundation
#if canImport(CryptoKit)
import CryptoKit
#endif

/// One downloadable GGUF: a GitHub release asset of this repo, pinned by exact size and SHA-256.
public struct ModelPinSpec: Equatable, Sendable {
    public let releaseTag: String
    public let fileName: String
    public let sizeBytes: Int64
    /// Full 64-hex lower-case SHA-256 of the file.
    public let sha256: String
    /// Label shown in the chat and saved nowhere else (history rows carry no model field,
    /// matching the bridge's shape).
    public let label: String

    public init(releaseTag: String, fileName: String, sizeBytes: Int64, sha256: String, label: String) {
        self.releaseTag = releaseTag
        self.fileName = fileName
        self.sizeBytes = sizeBytes
        self.sha256 = sha256
        self.label = label
    }

    public var url: URL {
        URL(string: "https://github.com/AxiomicCoreness/hello_world.py/releases/download/\(releaseTag)/\(fileName)")!
    }

    /// deepseek-r2 1.5B Q4_K_M (DeepSeek-R1-Distill-Qwen-1.5B fine-tune). The default.
    public static let deepseekR2_1p5b = ModelPinSpec(
        releaseTag: "model-deepseek-r2-1.5b-q4km-v1",
        fileName: "deepseek-r2-1.5b-Q4_K_M.gguf",
        sizeBytes: 1_117_320_640,
        sha256: "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1",
        label: "ClarkeYoursaTee (deepseek-r2-1.5b)")

    /// deepseek-r2 1.8B Q4_K_M (LLaMA-Pro block expansion, 28 → 33 layers). Available in code
    /// only: NOT the default until its eval has been reviewed.
    public static let deepseekR2_1p8b = ModelPinSpec(
        releaseTag: "model-deepseek-r2-1p8b-q4km-v1",
        fileName: "deepseek-r2-1p8b-Q4_K_M.gguf",
        sizeBytes: 1_259_979_680,
        sha256: "f19e0c500c4f734c6e8860e9f6e730e36d544c5f9500f74dce5339b188253af4",
        label: "ClarkeYoursaTee (deepseek-r2-1.8b)")

    /// Every pin the app knows about (selectable in code via `ModelPin.selected`).
    public static let all: [ModelPinSpec] = [deepseekR2_1p5b, deepseekR2_1p8b]
}

/// The model this app downloads on first launch. To switch models, change `selected` to another
/// `ModelPinSpec` (e.g. `.deepseekR2_1p8b`) — one line, compile-time. Each pin has its own file
/// name, so a downloaded file of one pin is never mistaken for another.
public enum ModelPin {
    /// Stays on the 1.5B until the 1.8B eval has been reviewed.
    public static let selected: ModelPinSpec = .deepseekR2_1p5b

    public static var releaseTag: String { selected.releaseTag }
    public static var fileName: String { selected.fileName }
    public static var url: URL { selected.url }
    public static var sizeBytes: Int64 { selected.sizeBytes }
    public static var sha256: String { selected.sha256 }
    public static var label: String { selected.label }
}

public enum VerifyError: Error, Equatable, CustomStringConvertible {
    case missing
    case wrongSize(expected: Int64, actual: Int64)
    case wrongHash(expected: String, actual: String)
    case notGGUF
    case cancelled

    public var description: String {
        switch self {
        case .missing: return "file not found"
        case let .wrongSize(e, a): return "size \(a) bytes, expected \(e)"
        case let .wrongHash(e, a): return "sha256 \(a), expected \(e)"
        case .notGGUF: return "not a GGUF file (magic bytes are not 'GGUF')"
        case .cancelled: return "verification cancelled"
        }
    }
}

public enum FileVerifier {
    /// Read size: big enough to be fast, small enough to keep memory flat on a 4 GB phone.
    public static let chunkSize = 4 * 1024 * 1024

    public static func fileSize(_ url: URL) -> Int64? {
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: url.path),
              let n = attrs[.size] as? NSNumber else { return nil }
        return n.int64Value
    }

    /// True when the first four bytes are the GGUF magic.
    public static func hasGGUFMagic(_ url: URL) -> Bool {
        guard let h = try? FileHandle(forReadingFrom: url) else { return false }
        defer { try? h.close() }
        let head = (try? h.read(upToCount: 4)) ?? Data()
        return head == Data("GGUF".utf8)
    }

    /// Streaming SHA-256 (lower-case hex). `progress` gets bytes hashed so far; return false from
    /// `shouldContinue` to stop early (throws `.cancelled`). Never loads the whole file.
    public static func sha256Hex(of url: URL,
                                 progress: ((Int64) -> Void)? = nil,
                                 shouldContinue: (() -> Bool)? = nil) throws -> String {
        guard let h = try? FileHandle(forReadingFrom: url) else { throw VerifyError.missing }
        defer { try? h.close() }
        var hasher = SHA256()
        var done: Int64 = 0
        while true {
            if let go = shouldContinue, !go() { throw VerifyError.cancelled }
            let chunk: Data = try autoreleasepoolCompat { try h.read(upToCount: chunkSize) ?? Data() }
            if chunk.isEmpty { break }
            hasher.update(data: chunk)
            done += Int64(chunk.count)
            progress?(done)
        }
        return hasher.finalize().map { String(format: "%02x", $0) }.joined()
    }

    /// Size first (cheap), then the full hash. Throws a `VerifyError` describing the mismatch.
    public static func verify(_ url: URL, expectedSize: Int64, expectedSHA256: String,
                              progress: ((Int64) -> Void)? = nil,
                              shouldContinue: (() -> Bool)? = nil) throws {
        guard let size = fileSize(url) else { throw VerifyError.missing }
        guard size == expectedSize else { throw VerifyError.wrongSize(expected: expectedSize, actual: size) }
        let got = try sha256Hex(of: url, progress: progress, shouldContinue: shouldContinue)
        guard got == expectedSHA256.lowercased() else {
            throw VerifyError.wrongHash(expected: expectedSHA256.lowercased(), actual: got)
        }
    }
}

/// `autoreleasepool` exists only on Apple platforms; it keeps each 4 MiB chunk from piling up.
@inline(__always)
func autoreleasepoolCompat<T>(_ body: () throws -> T) rethrows -> T {
    #if canImport(ObjectiveC)
    return try autoreleasepool(invoking: body)
    #else
    return try body()
    #endif
}
