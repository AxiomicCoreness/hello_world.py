// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
import XCTest
@testable import PocketCore
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

final class ServerV3tClientTests: XCTestCase {
    func testRejectsPlainHTTPRemoteAndEmptyToken() {
        XCTAssertThrowsError(try ServerV3tClient(base: "http://bridge.axiomiccoreness.com", token: "cyt_x"))
        XCTAssertThrowsError(try ServerV3tClient(base: "https://bridge.axiomiccoreness.com", token: ""))
        XCTAssertNoThrow(try ServerV3tClient(base: "http://127.0.0.1:8087", token: "cyt_x"))
    }

    func testChatRequestCarriesBearerAndConversation() throws {
        let c = try ServerV3tClient(base: "http://127.0.0.1:8087", token: "cyt_test")
        let r = try c.chatRequest(message: "hi", conversationID: "conv-1")
        XCTAssertEqual(r.url?.absoluteString, "http://127.0.0.1:8087/llm/v1/chat/completions")
        XCTAssertEqual(r.value(forHTTPHeaderField: "Authorization"), "Bearer cyt_test")
        let b = try JSONSerialization.jsonObject(with: r.httpBody!) as! [String: Any]
        XCTAssertEqual(b["conversation_id"] as? String, "conv-1")
    }

    func testParseChat() throws {
        let d = Data(#"{"conversation_id":"c","choices":[{"message":{"content":"ok"}}]}"#.utf8)
        let (t, c) = try ServerV3tClient.parseChat(d)
        XCTAssertEqual(t, "ok"); XCTAssertEqual(c, "c")
    }
}
