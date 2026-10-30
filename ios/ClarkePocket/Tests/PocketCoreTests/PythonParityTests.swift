// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The app writes the same history rows and normalises math the same way as the PC bridge
// (sovereign-irc-bridge/src/llm_chat.py + llm_markdown.py). Fixtures/python_vectors.json was
// produced by running those Python functions; these tests compare byte for byte.

import Foundation
import XCTest
@testable import PocketCore

final class PythonParityTests: XCTestCase {
    struct Vectors: Decodable {
        struct Pair: Decodable { var `in`: String; var out: String }
        struct Split: Decodable { var `in`: String; var answer: String; var thinking: String }
        struct EntryOut: Decodable { var content: String; var thinking: String? }
        struct Entry: Decodable { var answer: String; var thinking: String; var out: EntryOut }
        struct Row: Decodable {
            var role: String; var content: String; var format: String?; var thinking: String?
            var session: String; var ts: String; var json: String
        }
        struct Session: Decodable { var `in`: String?; var out: String }
        var normalize: [Pair]; var split: [Split]; var entry: [Entry]; var rows: [Row]; var session: [Session]
    }

    static let vectors: Vectors = {
        let url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("Fixtures/python_vectors.json")
        return try! JSONDecoder().decode(Vectors.self, from: Data(contentsOf: url))
    }()

    func testNormalizeMathMatchesPython() {
        XCTAssertGreaterThan(Self.vectors.normalize.count, 10)
        for v in Self.vectors.normalize {
            XCTAssertEqual(MarkdownMath.normalizeMath(v.in), v.out, "input: \(v.in.debugDescription)")
        }
    }

    func testSplitThinkingMatchesPython() {
        for v in Self.vectors.split {
            let (a, t) = MarkdownMath.splitThinking(v.in)
            XCTAssertEqual(a, v.answer, "answer for \(v.in.debugDescription)")
            XCTAssertEqual(t, v.thinking, "thinking for \(v.in.debugDescription)")
        }
    }

    func testMarkdownEntryMatchesPython() {
        for v in Self.vectors.entry {
            let e = MarkdownMath.markdownEntry(answer: v.answer, thinking: v.thinking)
            XCTAssertEqual(e.content, v.out.content)
            XCTAssertEqual(e.thinking, v.out.thinking)
        }
    }

    func testHistoryRowsAreByteIdenticalToPythonJsonDumps() {
        for v in Self.vectors.rows {
            let row = HistoryRow(role: HistoryRow.Role(rawValue: v.role)!, content: v.content, format: v.format,
                                 thinking: v.thinking, session: v.session, ts: v.ts)
            XCTAssertEqual(History.encode(row), v.json)
            // And it reads back.
            let back = History.decode(v.json)
            XCTAssertEqual(back?.content, v.content)
            XCTAssertEqual(back?.session, v.session)
        }
    }

    func testSessionNormalisationMatchesPython() {
        for v in Self.vectors.session {
            XCTAssertEqual(History.normalizeSession(v.in), v.out, "session \(String(describing: v.in))")
        }
    }
}
