// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// "Server (v3t)" engine: ClarkeYoursaTee-2B-v3t served by llama-server on the box, reached through
// the authenticated bridge route (sovereign-irc-bridge/src/v3t_route.py). Single-user: one owner
// bearer token, shared with the TeaVM browser page; one shared server-side SQLite history.
// The token is never in the app bundle or the repo — the app reads it from the Keychain
// (entered in Settings). No DB credentials exist on the phone at all.

import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public struct ServerV3tConversation: Codable, Equatable, Sendable {
    public var conversation_id: String
    public var created_at: String
    public var updated_at: String
    public var messages: Int
    public var title: String
    public var devices: [String]
}

public struct ServerV3tMessage: Codable, Equatable, Sendable {
    public var role: String
    public var content: String
    public var ts: String
    public var device: String?
    public var model_sha256: String?
}

public enum ServerV3tError: Error, Equatable {
    case noToken, badURL, unauthorized, http(Int), badReply
}

public struct ServerV3tClient: Sendable {
    /// Public bridge base (no token here). Override in Settings, e.g. http://127.0.0.1:8087 in a simulator.
    public static let defaultBase = "https://bridge.axiomiccoreness.com"
    public var base: URL
    public var token: String

    public init(base: String = ServerV3tClient.defaultBase, token: String) throws {
        guard let u = URL(string: base.trimmingCharacters(in: .whitespacesAndNewlines)),
              let scheme = u.scheme, scheme == "https" || (scheme == "http" && ServerV3tClient.isLoopback(u.host))
        else { throw ServerV3tError.badURL }
        guard !token.isEmpty else { throw ServerV3tError.noToken }
        self.base = u
        self.token = token
    }

    static func isLoopback(_ host: String?) -> Bool {
        host == "127.0.0.1" || host == "localhost" || host == "::1"
    }

    public func request(_ path: String, body: [String: Any]? = nil) throws -> URLRequest {
        guard let url = URL(string: path, relativeTo: base) else { throw ServerV3tError.badURL }
        var r = URLRequest(url: url)
        r.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        r.setValue("iphone", forHTTPHeaderField: "X-Client")
        r.timeoutInterval = 180
        if let body {
            r.httpMethod = "POST"
            r.setValue("application/json", forHTTPHeaderField: "Content-Type")
            r.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        return r
    }

    public func chatRequest(message: String, conversationID: String?, maxTokens: Int = 512) throws -> URLRequest {
        var b: [String: Any] = ["message": message, "max_tokens": maxTokens]
        if let conversationID { b["conversation_id"] = conversationID }
        return try request("/llm/v1/chat/completions", body: b)
    }

    /// → (reply text, conversation id)
    public static func parseChat(_ data: Data) throws -> (String, String) {
        guard let o = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let conv = o["conversation_id"] as? String,
              let ch = (o["choices"] as? [[String: Any]])?.first,
              let msg = ch["message"] as? [String: Any],
              let text = msg["content"] as? String else { throw ServerV3tError.badReply }
        return (text, conv)
    }

    static func check(_ resp: URLResponse) throws {
        guard let h = resp as? HTTPURLResponse else { throw ServerV3tError.badReply }
        if h.statusCode == 401 { throw ServerV3tError.unauthorized }
        guard (200..<300).contains(h.statusCode) else { throw ServerV3tError.http(h.statusCode) }
    }

    public func send(_ message: String, conversationID: String?) async throws -> (String, String) {
        let (d, r) = try await URLSession.shared.data(for: chatRequest(message: message, conversationID: conversationID))
        try Self.check(r)
        return try Self.parseChat(d)
    }

    public func conversations() async throws -> [ServerV3tConversation] {
        struct L: Codable { var conversations: [ServerV3tConversation] }
        let (d, r) = try await URLSession.shared.data(for: request("/llm/history"))
        try Self.check(r)
        return try JSONDecoder().decode(L.self, from: d).conversations
    }

    public func messages(_ conversationID: String) async throws -> [ServerV3tMessage] {
        struct F: Codable { var messages: [ServerV3tMessage] }
        let (d, r) = try await URLSession.shared.data(for: request("/llm/history/\(conversationID)"))
        try Self.check(r)
        return try JSONDecoder().decode(F.self, from: d).messages
    }
}
