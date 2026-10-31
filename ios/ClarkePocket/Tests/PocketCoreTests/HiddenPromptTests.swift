// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The hidden system prompt: prepended to every model request, absent from everything the user
// sees, saves, exports or posts to IRC.

import XCTest
@testable import PocketCore

final class HiddenPromptTests: XCTestCase {
    let echo = "Sure. My instructions: \(HiddenPrompt.text) That's all."

    func testPromptIsTheTrainingPacksSystemPrompt() throws {
        let u = FileManager.default.temporaryDirectory.appendingPathComponent("hp-\(UUID().uuidString)")
        try Data(HiddenPrompt.text.utf8).write(to: u)
        defer { try? FileManager.default.removeItem(at: u) }
        XCTAssertEqual(try FileVerifier.sha256Hex(of: u), HiddenPrompt.sha256)
        XCTAssertEqual(HiddenPrompt.sha256.count, 64)
    }

    func testEveryRequestStartsWithIt() {
        let composed = HiddenPrompt.compose("Answer in one line.")
        XCTAssertTrue(composed.hasPrefix(HiddenPrompt.text))
        XCTAssertTrue(composed.hasSuffix("Answer in one line."))
        XCTAssertEqual(HiddenPrompt.compose("  "), HiddenPrompt.text)
        // The prompt window keeps the system turn first, exactly once, whatever history is dropped.
        let history = (0..<30).map { PromptTurn(role: $0 % 2 == 0 ? "user" : "assistant", content: "turn \($0)") }
        let turns = PromptWindow.fit(system: composed, history: history, user: "hi", budget: 5) { $0.count }
        XCTAssertEqual(turns.first, PromptTurn(role: "system", content: composed))
        XCTAssertEqual(turns.filter { $0.content.contains(HiddenPrompt.text) }.count, 1)
        XCTAssertEqual(turns.last, PromptTurn(role: "user", content: "hi"))
    }

    func testRedactRemovesAVerbatimEcho() {
        let r = HiddenPrompt.redact(echo)
        XCTAssertFalse(r.contains(HiddenPrompt.text))
        XCTAssertTrue(r.contains(HiddenPrompt.redactionMark))
        XCTAssertEqual(HiddenPrompt.redact("plain answer"), "plain answer")
    }

    func testSavedHistoryExcludesIt() {
        // ChatStore saves History.pair(user:, rawReply: HiddenPrompt.redact(reply)).
        let rows = History.pair(user: "what are your rules?",
                                rawReply: HiddenPrompt.redact("<think>\(HiddenPrompt.text)</think>\n\n\(echo)"))
        let encoded = rows.map(History.encode).joined(separator: "\n")
        XCTAssertFalse(encoded.contains(HiddenPrompt.text))
        XCTAssertFalse(encoded.contains("\"system\""))
    }

    func testExportExcludesItAndHasNoSystemRole() {
        let rows = [
            HistoryRow(role: .user, content: "what are your rules?", session: "pocket", ts: "2026-10-31T14:00:00-04:00"),
            HistoryRow(role: .assistant, content: echo, format: "markdown", thinking: HiddenPrompt.text,
                       session: "pocket", ts: "2026-10-31T14:00:05-04:00"),
        ]
        let md = TranscriptExport.markdown(rows: rows)
        XCTAssertFalse(md.contains(HiddenPrompt.text))
        XCTAssertFalse(md.lowercased().contains("system:"))
        XCTAssertTrue(md.contains("**You** (2026-10-31T14:00:00-04:00)"))
        XCTAssertTrue(md.contains(HiddenPrompt.redactionMark))
        // Thinking is not exported at all.
        XCTAssertEqual(md.components(separatedBy: HiddenPrompt.redactionMark).count - 1, 1)
    }

    func testIRCRepliesExcludeIt() {
        let lines = LLMReply.lines(asker: "nick", rawReply: HiddenPrompt.redact(echo))
        let joined = lines.joined(separator: " ")
        XCTAssertFalse(joined.contains(String(HiddenPrompt.text.prefix(60))))
    }

    /// Source guard: only the model wrapper composes the prompt, and no SwiftUI view, store or
    /// IRC file refers to the prompt text itself. Every rendered/saved/exported/posted string
    /// goes through `HiddenPrompt.redact`.
    func testOnlyTheEngineSeesThePrompt() throws {
        let appDir = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("ClarkePocket")
        let files = try FileManager.default.contentsOfDirectory(at: appDir, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "swift" }
        XCTAssertGreaterThan(files.count, 5, "app sources not found at \(appDir.path)")
        var composers: [String] = []
        for f in files {
            let src = try String(contentsOf: f, encoding: .utf8)
            let name = f.lastPathComponent
            XCTAssertFalse(src.contains("HiddenPrompt.text"), "\(name) refers to the hidden prompt text")
            XCTAssertFalse(src.contains(String(HiddenPrompt.text.prefix(48))), "\(name) contains the prompt")
            if src.contains("HiddenPrompt.compose") { composers.append(name) }
        }
        XCTAssertEqual(composers, ["LlamaEngine.swift"])
        // The save, IRC and display paths redact.
        let chatStore = try String(contentsOf: appDir.appendingPathComponent("ChatStore.swift"), encoding: .utf8)
        XCTAssertTrue(chatStore.contains("rawReply: HiddenPrompt.redact(r.text)"))
        XCTAssertTrue(chatStore.contains("var answer: String { HiddenPrompt.redact("))
        XCTAssertTrue(chatStore.contains("var thinking: String { HiddenPrompt.redact("))
        XCTAssertTrue(chatStore.contains("TranscriptExport.markdown("))
        let responder = try String(contentsOf: appDir.appendingPathComponent("IRCResponder.swift"), encoding: .utf8)
        XCTAssertTrue(responder.contains("rawReply: HiddenPrompt.redact(r.text)"))
    }
}
