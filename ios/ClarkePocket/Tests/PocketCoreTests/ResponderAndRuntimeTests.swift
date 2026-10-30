// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import PocketCore

final class ResponderTests: XCTestCase {
    func testTrigger() {
        let t = LLMReply.trigger(sender: "bob", target: "#c", text: "!LLM  what is 2+2", ownNick: "Clarke_iOS_1")
        XCTAssertEqual(t?.asker, "bob")
        XCTAssertEqual(t?.question, "what is 2+2")
        XCTAssertNil(LLMReply.trigger(sender: "bob", target: "Clarke_iOS_1", text: "!llm hi", ownNick: "Clarke_iOS_1"))
        XCTAssertNil(LLMReply.trigger(sender: "Clarke_iOS_1", target: "#c", text: "!llm hi", ownNick: "clarke_ios_1"))
        XCTAssertNil(LLMReply.trigger(sender: "bob", target: "#c", text: "!llmhi", ownNick: "me"))
        XCTAssertNil(LLMReply.trigger(sender: "bob", target: "#c", text: "!llm    ", ownNick: "me"))
        XCTAssertNil(LLMReply.trigger(sender: "bot", target: "#c", text: "[LLM] bob: !llm loop", ownNick: "me"))
    }

    func testLinesStripThinkingAndWrap() {
        let l = LLMReply.lines(asker: "bob", rawReply: "<think>private</think>\n\nFive.\n\nThat's it.")
        XCTAssertEqual(l, ["[LLM] bob: Five. That's it."])
        XCTAssertEqual(LLMReply.lines(asker: "bob", rawReply: "<think>never closed"),
                       ["[LLM] bob: (no answer within the token limit)"])
        let long = LLMReply.lines(asker: "bob", rawReply: Array(repeating: "wörd", count: 1000).joined(separator: " "))
        XCTAssertEqual(long.count, LLMReply.maxLines)
        XCTAssertTrue(long.last!.hasSuffix(" …"))
        for line in long {
            XCTAssertTrue(line.hasPrefix("[LLM] "))
            XCTAssertLessThanOrEqual(line.utf8.count, IRCOutgoing.maxTextBytes)
        }
        let two = LLMReply.lines(asker: "b", rawReply: Array(repeating: "x", count: 250).joined(separator: " "))
        XCTAssertEqual(two.count, 2)
        XCTAssertFalse(two.last!.hasSuffix(" …"))
        for line in LLMReply.lines(asker: "b", rawReply: "a\u{1}ACTION b\r\nc") {
            XCTAssertFalse(line.contains("\u{1}")); XCTAssertFalse(line.contains("\r")); XCTAssertFalse(line.contains("\n"))
        }
    }

    func testRateLimiter() {
        var r = LLMRateLimiter()
        let t0 = Date(timeIntervalSince1970: 0)
        XCTAssertTrue(r.begin(nick: "a", now: t0))
        XCTAssertFalse(r.begin(nick: "b", now: t0.addingTimeInterval(20)))   // busy
        r.finish()
        XCTAssertFalse(r.begin(nick: "b", now: t0.addingTimeInterval(10)))   // global 15 s
        XCTAssertTrue(r.begin(nick: "b", now: t0.addingTimeInterval(16)))
        r.finish()
        XCTAssertFalse(r.begin(nick: "a", now: t0.addingTimeInterval(40)))   // per-nick 60 s
        XCTAssertTrue(r.begin(nick: "a", now: t0.addingTimeInterval(61)))
    }
}

final class RuntimeTests: XCTestCase {
    func testThreadsForA14AndOthers() {
        XCTAssertEqual(RuntimePolicy.threads(performanceCores: 2, totalCores: 6).gen, 2)   // iPhone 12
        XCTAssertEqual(RuntimePolicy.threads(performanceCores: 2, totalCores: 6).batch, 4)
        XCTAssertEqual(RuntimePolicy.threads(performanceCores: nil, totalCores: 6).gen, 2)
        XCTAssertEqual(RuntimePolicy.threads(performanceCores: 1, totalCores: 1).gen, 1)
        XCTAssertEqual(RuntimePolicy.threads(performanceCores: 8, totalCores: 4).gen, 3)
    }

    func testMemoryAdvice() {
        let m = ModelPin.sizeBytes
        XCTAssertEqual(RuntimePolicy.memoryAdvice(available: 0, modelBytes: m), .unknown)
        XCTAssertEqual(RuntimePolicy.memoryAdvice(available: 3_000_000_000, modelBytes: m), .ok)
        if case .low(let need, _) = RuntimePolicy.memoryAdvice(available: 500_000_000, modelBytes: m) {
            XCTAssertGreaterThan(need, 500_000_000)
        } else { XCTFail() }
        XCTAssertEqual(RuntimePolicy.formatBytes(1_117_320_640), "1.12 GB")
        XCTAssertEqual(RuntimePolicy.formatBytes(57_000_000), "57 MB")
    }

    func testBOSDecision() {
        let r1 = "{% if not add_generation_prompt is defined %}...{{ bos_token }}{{ ns.system_prompt }}"
        XCTAssertTrue(RuntimePolicy.shouldPrependBOS(template: r1, vocabAddsBOS: false, promptStartsWithBOS: false))
        XCTAssertFalse(RuntimePolicy.shouldPrependBOS(template: r1, vocabAddsBOS: true, promptStartsWithBOS: false))
        XCTAssertFalse(RuntimePolicy.shouldPrependBOS(template: r1, vocabAddsBOS: false, promptStartsWithBOS: true))
        XCTAssertFalse(RuntimePolicy.shouldPrependBOS(template: "<|im_start|>", vocabAddsBOS: false, promptStartsWithBOS: false))
        XCTAssertFalse(RuntimePolicy.shouldPrependBOS(template: nil, vocabAddsBOS: false, promptStartsWithBOS: false))
    }

    func testPromptWindowKeepsNewestThatFits() {
        let hist = (1...6).flatMap { [PromptTurn(role: "user", content: "u\($0)"), PromptTurn(role: "assistant", content: "a\($0)")] }
        // Stand-in tokenizer: 10 tokens per turn.
        let fit = PromptWindow.fit(system: "S", history: hist, user: "now", budget: 60) { $0.count * 10 }
        XCTAssertEqual(fit.map(\.content), ["S", "u5", "a5", "u6", "a6", "now"])
        // An odd budget would leave an orphan assistant first → dropped.
        let odd = PromptWindow.fit(system: "S", history: hist, user: "now", budget: 50) { $0.count * 10 }
        XCTAssertEqual(odd.map(\.content), ["S", "u6", "a6", "now"])
        let none = PromptWindow.fit(system: "S", history: hist, user: "now", budget: 5) { $0.count * 10 }
        XCTAssertEqual(none.map(\.content), ["S", "now"])
    }
}

final class UTF8AssemblerTests: XCTestCase {
    func testSplitMultibyte() {
        var a = UTF8Assembler()
        let bytes = Array("aé😀φ".utf8)  // 1 + 2 + 4 + 2
        var out = ""
        for b in bytes { out += a.push([b]) }
        out += a.flush()
        XCTAssertEqual(out, "aé😀φ")
        var b = UTF8Assembler()
        XCTAssertEqual(b.push([0xF0, 0x9F]), "")
        XCTAssertEqual(b.push([0x98, 0x80, 0x41]), "😀A")
        var c = UTF8Assembler()
        XCTAssertEqual(c.push([0xE2, 0x82]), "")
        XCTAssertEqual(c.flush(), "\u{FFFD}")
        var d = UTF8Assembler()
        XCTAssertEqual(d.push([0xFF, 0x41]), "\u{FFFD}A")
    }
}
