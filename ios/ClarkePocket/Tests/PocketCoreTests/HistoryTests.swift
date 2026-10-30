// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import PocketCore

final class HistoryTests: XCTestCase {
    let ny = TimeZone(identifier: "America/New_York")!

    func testTimestampUsesLocalOffsetNeverZ() {
        let d = Date(timeIntervalSince1970: 1_793_396_400) // 2026-10-30T17:40:00-04:00
        XCTAssertEqual(History.timestamp(d, timeZone: ny), "2026-10-30T17:40:00-04:00")
        XCTAssertEqual(History.timestamp(d, timeZone: TimeZone(identifier: "UTC")!), "2026-10-30T21:40:00+00:00")
        XCTAssertEqual(History.timestamp(d, timeZone: TimeZone(identifier: "Asia/Kolkata")!), "2026-10-31T03:10:00+05:30")
    }

    func testPairSplitsThinkingAndNormalises() {
        let rows = History.pair(user: "q", rawReply: "<think>\nhmm \\[x\\]\n</think>\n\nIt is \\[y\\].",
                                date: Date(timeIntervalSince1970: 1_793_396_400), timeZone: ny)
        XCTAssertEqual(rows.count, 2)
        XCTAssertEqual(History.encode(rows[0]),
                       #"{"role": "user", "content": "q", "session": "pocket", "ts": "2026-10-30T17:40:00-04:00"}"#)
        XCTAssertEqual(History.encode(rows[1]),
                       #"{"role": "assistant", "content": "It is $$y$$.", "format": "markdown", "thinking": "hmm $$x$$", "session": "pocket", "ts": "2026-10-30T17:40:00-04:00"}"#)
    }

    func testDecodeIsTolerant() {
        let text = """
        {"role": "user", "content": "a", "session": "pocket", "ts": "t"}
        not json
        {"role": "system", "content": "skip"}
        {"role": "assistant", "content": 5}

        {"role": "assistant", "content": "legacy", "thinking": "ignored without format"}
        {"role": "assistant", "content": "b", "format": "markdown", "thinking": "t", "session": "bad session"}
        """
        let rows = History.decodeAll(text)
        XCTAssertEqual(rows.map(\.content), ["a", "legacy", "b"])
        XCTAssertNil(rows[1].thinking)
        XCTAssertEqual(rows[2].thinking, "t")
        XCTAssertEqual(rows[2].session, "default")
    }

    func testFileAppendReadArchive() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: dir) }
        let f = HistoryFile(url: dir.appendingPathComponent("llm_history.jsonl"))
        XCTAssertTrue(f.readAll().isEmpty)
        XCTAssertTrue(f.append(History.pair(user: "1", rawReply: "one")))
        XCTAssertTrue(f.append(History.pair(user: "2", rawReply: "two")))
        XCTAssertEqual(f.readAll().map(\.content), ["1", "one", "2", "two"])
        let raw = try String(contentsOf: f.url, encoding: .utf8)
        XCTAssertEqual(raw.filter { $0 == "\n" }.count, 4)
        let archived = try XCTUnwrap(f.archive())
        XCTAssertTrue(archived.lastPathComponent.hasPrefix("llm_history.jsonl.reset-pocket-"))
        XCTAssertFalse(FileManager.default.fileExists(atPath: f.url.path))
        XCTAssertTrue(f.readAll().isEmpty)
        XCTAssertNil(f.archive())
    }

    func testPromptTurnsUseAnswersOnly() {
        let rows = History.pair(user: "q", rawReply: "<think>secret</think>ans")
        XCTAssertEqual(PromptWindow.turns(from: rows),
                       [PromptTurn(role: "user", content: "q"), PromptTurn(role: "assistant", content: "ans")])
    }
}
