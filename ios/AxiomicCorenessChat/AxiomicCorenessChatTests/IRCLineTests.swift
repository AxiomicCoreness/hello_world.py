// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Pure-Swift tests for IRCLine.swift (no network, no UI). In Xcode: add a Unit Testing Bundle
// target and add this file to it (see README). The repo has no macOS CI job, so these are not
// run in GitHub Actions.

import XCTest
#if canImport(AxiomicCorenessChat)
@testable import AxiomicCorenessChat
#endif

final class IRCLineTests: XCTestCase {
    func testWelcomeNumeric() throws {
        let l = try XCTUnwrap(IRCLine.parse(":tungsten.libera.chat 001 Clarke_iOS_1234 :Welcome to the Libera.Chat Internet Relay Chat Network Clarke_iOS_1234\r\n"))
        XCTAssertEqual(l.prefix, "tungsten.libera.chat")
        XCTAssertEqual(l.nick, "tungsten.libera.chat")
        XCTAssertEqual(l.command, "001")
        XCTAssertEqual(l.params.first, "Clarke_iOS_1234")
        XCTAssertEqual(l.trailing, "Welcome to the Libera.Chat Internet Relay Chat Network Clarke_iOS_1234")
        XCTAssertEqual(l.params.count, 2)
    }

    func testPrivmsgWithTagsAndPrefix() throws {
        let l = try XCTUnwrap(IRCLine.parse("@time=2026-10-30T19:20:00.000Z;msgid=ab\\:c\\sd;bot :llmbot!~llm@user/clarke PRIVMSG #axiomiccoreness :φ = (1+√5)/2 : golden"))
        XCTAssertEqual(l.tags["time"], "2026-10-30T19:20:00.000Z")
        XCTAssertEqual(l.tags["msgid"], "ab;c d")
        XCTAssertEqual(l.tags["bot"], "")
        XCTAssertEqual(l.nick, "llmbot")
        XCTAssertEqual(l.command, "PRIVMSG")
        XCTAssertEqual(l.params, ["#axiomiccoreness", "φ = (1+√5)/2 : golden"])
    }

    func testPingWithoutPrefixAndLowercaseCommand() throws {
        let l = try XCTUnwrap(IRCLine.parse("ping :tungsten.libera.chat"))
        XCTAssertNil(l.prefix)
        XCTAssertNil(l.nick)
        XCTAssertEqual(l.command, "PING")
        XCTAssertEqual(l.params, ["tungsten.libera.chat"])
    }

    func testNickInUse433AndNoTrailing() throws {
        let a = try XCTUnwrap(IRCLine.parse(":srv 433 * Clarke_iOS_1234 :Nickname is already in use."))
        XCTAssertEqual(a.command, "433")
        XCTAssertEqual(a.params, ["*", "Clarke_iOS_1234", "Nickname is already in use."])
        let b = try XCTUnwrap(IRCLine.parse(":nick!u@h JOIN #axiomiccoreness"))
        XCTAssertNil(b.trailing)
        XCTAssertEqual(b.params, ["#axiomiccoreness"])
        let c = try XCTUnwrap(IRCLine.parse(":nick!u@h PRIVMSG #c :"))
        XCTAssertEqual(c.trailing, "")
        XCTAssertEqual(c.params, ["#c", ""])
    }

    func testExtraSpacesAndEmpty() {
        XCTAssertNil(IRCLine.parse(""))
        XCTAssertNil(IRCLine.parse("\r\n"))
        XCTAssertNil(IRCLine.parse("@a=b "))
        XCTAssertEqual(IRCLine.parse(":p  MODE   #c  +o  x")?.params, ["#c", "+o", "x"])
    }

    func testSplitFrame() {
        XCTAssertEqual(IRCLine.splitFrame("PING :x"), ["PING :x"])
        XCTAssertEqual(IRCLine.splitFrame("A\r\nB\r\n"), ["A", "B"])
        XCTAssertEqual(IRCLine.splitFrame("A\nB\n\nC"), ["A", "B", "C"])
        XCTAssertEqual(IRCLine.splitFrame("\r\n"), [])
    }

    func testSanitizeStripsCRLFAndCaps() {
        XCTAssertEqual(IRCOutgoing.sanitize("  !llm hi\r\nQUIT :pwned \u{0} "), "!llm hi  QUIT :pwned")
        XCTAssertFalse(IRCOutgoing.sanitize("a\rb\nc").contains(where: { $0 == "\r" || $0 == "\n" }))
        let long = String(repeating: "φ", count: 300)  // 2 bytes each = 600 bytes
        let cut = IRCOutgoing.sanitize(long)
        XCTAssertLessThanOrEqual(cut.utf8.count, IRCOutgoing.maxTextBytes)
        XCTAssertEqual(cut.utf8.count, 400)
        XCTAssertEqual(IRCOutgoing.sanitize("😀😀", maxBytes: 5), "😀")  // never splits a character
    }

    func testThinkingBlockFromBot() {
        var t = ThinkingTracker()
        XCTAssertTrue(t.isThinking(sender: "llmbot", text: "[ClarkeYoursaTee (deepseek-r2-1.5b)] [thinking]"))
        XCTAssertTrue(t.isThinking(sender: "llmbot", text: "Okay, so the user asks about φ."))
        XCTAssertFalse(t.isThinking(sender: "someone", text: "hello"))   // other nicks unaffected
        XCTAssertTrue(t.isThinking(sender: "LLMBOT", text: "[/thinking]"))
        XCTAssertFalse(t.isThinking(sender: "llmbot", text: "φ ≈ 1.618"))
        XCTAssertTrue(t.isThinking(sender: "llmbot",
            text: "[ClarkeYoursaTee (deepseek-r2-1.5b)] (thinking: 12 line(s) hidden; IRC_SHOW_THINKING=1 shows them)"))
        XCTAssertFalse(t.isThinking(sender: "llmbot", text: "[ClarkeYoursaTee (deepseek-r2-1.5b)] The answer is 2."))
        _ = t.isThinking(sender: "llmbot", text: "[thinking]")
        t.reset()
        XCTAssertFalse(t.isThinking(sender: "llmbot", text: "after reset"))
    }
}
