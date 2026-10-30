// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import PocketCore
#if canImport(CryptoKit)
import CryptoKit
#endif

final class VerifierTests: XCTestCase {
    var dir: URL!

    override func setUp() {
        dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }
    override func tearDown() { try? FileManager.default.removeItem(at: dir) }

    func file(_ name: String, _ data: Data) -> URL {
        let u = dir.appendingPathComponent(name)
        try! data.write(to: u)
        return u
    }

    // NIST FIPS 180-4 examples + edge sizes around the 64-byte block / 4 MiB chunk.
    func testKnownVectors() throws {
        let cases: [(Data, String)] = [
            (Data(), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            (Data("abc".utf8), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
            (Data("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq".utf8),
             "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"),
            (Data(repeating: 0x61, count: 1_000_000), "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"),
        ]
        for (i, (d, hex)) in cases.enumerated() {
            XCTAssertEqual(try FileVerifier.sha256Hex(of: file("v\(i)", d)), hex)
        }
    }

    func testChunkBoundaryAndProgress() throws {
        // 4 MiB + 1 byte crosses the read-chunk boundary; compare against a single-shot hash.
        var d = Data(count: FileVerifier.chunkSize + 1)
        for i in 0..<d.count { d[i] = UInt8(truncatingIfNeeded: i &* 31 &+ 7) }
        let u = file("big", d)
        var seen: [Int64] = []
        let streamed = try FileVerifier.sha256Hex(of: u, progress: { seen.append($0) })
        XCTAssertEqual(seen, [Int64(FileVerifier.chunkSize), Int64(d.count)])
        var h = SHA256(); h.update(data: d)
        XCTAssertEqual(streamed, h.finalize().map { String(format: "%02x", $0) }.joined())
    }

    func testVerifyOutcomes() throws {
        let d = Data("GGUF-and-some-bytes".utf8)
        let u = file("m.gguf", d)
        let good = try FileVerifier.sha256Hex(of: u)
        XCTAssertNoThrow(try FileVerifier.verify(u, expectedSize: Int64(d.count), expectedSHA256: good.uppercased()))
        XCTAssertThrowsError(try FileVerifier.verify(u, expectedSize: 5, expectedSHA256: good)) {
            XCTAssertEqual($0 as? VerifyError, .wrongSize(expected: 5, actual: Int64(d.count)))
        }
        let bad = String(repeating: "0", count: 64)
        XCTAssertThrowsError(try FileVerifier.verify(u, expectedSize: Int64(d.count), expectedSHA256: bad)) {
            XCTAssertEqual($0 as? VerifyError, .wrongHash(expected: bad, actual: good))
        }
        XCTAssertThrowsError(try FileVerifier.verify(dir.appendingPathComponent("nope"), expectedSize: 1, expectedSHA256: bad)) {
            XCTAssertEqual($0 as? VerifyError, .missing)
        }
        XCTAssertThrowsError(try FileVerifier.sha256Hex(of: u, shouldContinue: { false })) {
            XCTAssertEqual($0 as? VerifyError, .cancelled)
        }
    }

    func testGGUFMagic() {
        XCTAssertTrue(FileVerifier.hasGGUFMagic(file("a", Data("GGUF\u{3}\0\0\0".utf8))))
        XCTAssertFalse(FileVerifier.hasGGUFMagic(file("b", Data("GGU".utf8))))
        XCTAssertFalse(FileVerifier.hasGGUFMagic(file("c", Data("<html>".utf8))))
        XCTAssertFalse(FileVerifier.hasGGUFMagic(dir.appendingPathComponent("missing")))
    }

    func testPinnedModelConstants() {
        XCTAssertEqual(ModelPin.sizeBytes, 1_117_320_640)
        XCTAssertEqual(ModelPin.sha256.count, 64)
        XCTAssertEqual(ModelPin.url.absoluteString,
                       "https://github.com/AxiomicCoreness/hello_world.py/releases/download/model-deepseek-r2-1.5b-q4km-v1/deepseek-r2-1.5b-Q4_K_M.gguf")
    }

    /// Optional: hash the real 1.1 GB model when POCKET_REAL_GGUF points at it (skipped in CI).
    func testRealModelIfPresent() throws {
        guard let p = ProcessInfo.processInfo.environment["POCKET_REAL_GGUF"] else {
            throw XCTSkip("set POCKET_REAL_GGUF=/path/to/deepseek-r2-1.5b-Q4_K_M.gguf to run")
        }
        let u = URL(fileURLWithPath: p)
        XCTAssertTrue(FileVerifier.hasGGUFMagic(u))
        XCTAssertNoThrow(try FileVerifier.verify(u, expectedSize: ModelPin.sizeBytes, expectedSHA256: ModelPin.sha256))
    }
}
