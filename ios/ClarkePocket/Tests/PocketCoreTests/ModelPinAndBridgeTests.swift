// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The selectable model pin (1.5B stays the default) and the PC-bot fallback's pure logic.

import XCTest
@testable import PocketCore

final class ModelPinSelectionTests: XCTestCase {
    func testDefaultIsStillThe1p5B() {
        // The 1.8B is available in code but is not the default until its eval has been reviewed.
        XCTAssertEqual(ModelPin.selected, ModelPinSpec.deepseekR2_1p5b)
        XCTAssertEqual(ModelPin.fileName, "deepseek-r2-1.5b-Q4_K_M.gguf")
        XCTAssertEqual(ModelPin.sizeBytes, 1_117_320_640)
        XCTAssertEqual(ModelPin.sha256, "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1")
    }

    func testEveryPinIsFullyPinned() {
        let hex = CharacterSet(charactersIn: "0123456789abcdef")
        for p in ModelPinSpec.all {
            XCTAssertEqual(p.sha256.count, 64, p.fileName)
            XCTAssertTrue(p.sha256.unicodeScalars.allSatisfy { hex.contains($0) }, p.fileName)
            XCTAssertGreaterThan(p.sizeBytes, 0)
            XCTAssertTrue(p.fileName.hasSuffix(".gguf"))
            XCTAssertEqual(p.url.absoluteString,
                           "https://github.com/AxiomicCoreness/hello_world.py/releases/download/\(p.releaseTag)/\(p.fileName)")
            XCTAssertEqual(p.url.scheme, "https")
        }
        // Distinct file names: switching pins never reuses another pin's file.
        XCTAssertEqual(Set(ModelPinSpec.all.map(\.fileName)).count, ModelPinSpec.all.count)
    }

    func testThe1p8BPinMatchesItsRelease() {
        let p = ModelPinSpec.deepseekR2_1p8b
        XCTAssertEqual(p.releaseTag, "model-deepseek-r2-1p8b-q4km-v1")
        XCTAssertEqual(p.fileName, "deepseek-r2-1p8b-Q4_K_M.gguf")
        XCTAssertEqual(p.sizeBytes, 1_259_979_680)
        XCTAssertEqual(p.sha256, "f19e0c500c4f734c6e8860e9f6e730e36d544c5f9500f74dce5339b188253af4")
    }

    func testVerifierRejectsTheOtherPinsSize() throws {
        // A 1.5B-sized file must never verify as the 1.8B (size is checked before the hash).
        let u = FileManager.default.temporaryDirectory.appendingPathComponent("pin-\(UUID().uuidString).gguf")
        try Data("GGUF".utf8).write(to: u)
        defer { try? FileManager.default.removeItem(at: u) }
        let p = ModelPinSpec.deepseekR2_1p8b
        XCTAssertThrowsError(try FileVerifier.verify(u, expectedSize: p.sizeBytes, expectedSHA256: p.sha256)) {
            XCTAssertEqual($0 as? VerifyError, .wrongSize(expected: p.sizeBytes, actual: 4))
        }
    }
}

final class BridgeFallbackLogicTests: XCTestCase {
    let t0 = Date(timeIntervalSince1970: 1_800_000_000)

    func testPMTextIsOneSafeLine() {
        XCTAssertEqual(BridgeRequest.pmText(question: "what is 2+3?"), "!llm what is 2+3?")
        XCTAssertEqual(BridgeRequest.pmText(question: "line one\r\nline two\nthree"), "!llm line one line two three")
        XCTAssertEqual(BridgeRequest.pmText(question: "\u{1}VERSION\u{1}"), "!llm VERSION")
        XCTAssertNil(BridgeRequest.pmText(question: "  \n "))
        let long = BridgeRequest.pmText(question: String(repeating: "é", count: 500))!
        XCTAssertLessThanOrEqual(long.utf8.count, IRCOutgoing.maxTextBytes)
        XCTAssertFalse(long.contains("\r") || long.contains("\n"))
    }

    func testCollectsTaggedLinesFromTheBotOnly() {
        var c = BridgeReplyCollector(startedAt: t0)
        XCTAssertEqual(c.state(now: t0.addingTimeInterval(1)), .waiting)
        XCTAssertNil(c.accept(sender: "someone", text: "[LLM] fake", isNotice: false, now: t0))
        XCTAssertEqual(c.accept(sender: "clarketutorbot", text: "[LLM] [ClarkeYoursaTee (deepseek-r2-1.5b)] 2 plus 3 is 5.",
                                isNotice: false, now: t0.addingTimeInterval(10)),
                       "[ClarkeYoursaTee (deepseek-r2-1.5b)] 2 plus 3 is 5.")
        XCTAssertNil(c.accept(sender: "ClarkeTutorBot", text: "[LLM] (thinking: 3 line(s) hidden; IRC_SHOW_THINKING=1 shows them)",
                              isNotice: false, now: t0.addingTimeInterval(10)))
        XCTAssertEqual(c.accept(sender: "ClarkeTutorBot", text: "[LLM] Second line.", isNotice: false, now: t0.addingTimeInterval(11)),
                       "Second line.")
        XCTAssertEqual(c.state(now: t0.addingTimeInterval(13)), .receiving)
        XCTAssertEqual(c.state(now: t0.addingTimeInterval(15)), .done)
        XCTAssertEqual(c.text, "[ClarkeYoursaTee (deepseek-r2-1.5b)] 2 plus 3 is 5.\nSecond line.")
    }

    func testTruncatedMarkerEndsAtOnce() {
        var c = BridgeReplyCollector(startedAt: t0)
        _ = c.accept(sender: "ClarkeTutorBot", text: "[LLM] a", isNotice: false, now: t0)
        _ = c.accept(sender: "ClarkeTutorBot", text: "[LLM] …(truncated)", isNotice: false, now: t0)
        XCTAssertEqual(c.state(now: t0), .done)
        XCTAssertNil(c.accept(sender: "ClarkeTutorBot", text: "[LLM] late", isNotice: false, now: t0))
    }

    func testNoticeEndsWithoutText() {
        var c = BridgeReplyCollector(startedAt: t0)
        XCTAssertNil(c.accept(sender: "ClarkeTutorBot", text: "slow down: one !llm question per 15s per nick (try again in ~9s)",
                              isNotice: true, now: t0))
        XCTAssertEqual(c.state(now: t0), .done)
        XCTAssertEqual(c.text, "")
        XCTAssertEqual(c.notice, "slow down: one !llm question per 15s per nick (try again in ~9s)")
    }

    func testTimesOutWhenTheBotIsOff() {
        let c = BridgeReplyCollector(startedAt: t0, firstLineTimeout: 180)
        XCTAssertEqual(c.state(now: t0.addingTimeInterval(179)), .waiting)
        XCTAssertEqual(c.state(now: t0.addingTimeInterval(180)), .timedOut)
    }
}
