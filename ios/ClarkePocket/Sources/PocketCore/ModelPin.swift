// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The pinned on-device model and a streaming SHA-256 file verifier.
// The app (iOS) hashes with CryptoKit. Linux has no CryptoKit, so there — only for `swift test` —
// the same calls go to the small pure-Swift `SHA256` in SHA256Fallback.swift (same API subset).

import Foundation
#if canImport(CryptoKit)
import CryptoKit
#endif

/// The one model this app downloads by default (GitHub release asset of this repo).
public enum ModelPin {
    public static let releaseTag = "model-deepseek-r2-1.5b-q4km-v1"
    public static let fileName = "deepseek-r2-1.5b-Q4_K_M.gguf"
    public static let url = URL(string:
        "https://github.com/AxiomicCoreness/hello_world.py/releases/download/\(releaseTag)/\(fileName)")!
    public static let sizeBytes: Int64 = 1_117_320_640
    public static let sha256 = "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1"
    /// Label shown in the chat and saved nowhere else (the history rows carry no model field,
    /// matching the bridge's shape).
    public static let label = "ClarkeYoursaTee (deepseek-r2-1.5b)"
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
