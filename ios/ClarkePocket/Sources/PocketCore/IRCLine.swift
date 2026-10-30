// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Copied (not moved) from ios/AxiomicCorenessChat/AxiomicCorenessChat/IRCLine.swift on
// feat/ios-libera-chat @ db2b966bc03d153803ee174415843b2134c35a1e (PR #165). Unchanged below.
//
// Pure-Foundation IRC helpers: line parsing, frame splitting, outgoing-text sanitising and
// the bot's [thinking] block tracking. No UIKit/SwiftUI here, so the unit tests in
// Tests/PocketCoreTests/ can run on any Swift toolchain (including Linux `swift test`).

import Foundation

/// One parsed IRC protocol line: `[@tags] [:prefix] COMMAND [params...] [:trailing]`.
public struct IRCLine: Equatable, Sendable {
    /// IRCv3 message tags (`@k=v;k2`), values unescaped. Empty when the line has none.
    public var tags: [String: String]
    /// Raw source prefix without the leading `:`, e.g. `nick!user@host` or `server.name`.
    public var prefix: String?
    /// Command or 3-digit numeric, upper-cased (`PRIVMSG`, `001`, `433`, ...).
    public var command: String
    /// Middle params followed by the trailing param (if any) as the last element.
    public var params: [String]
    /// The trailing param (text after ` :`), or nil when the line had none.
    public var trailing: String?

    /// Nick part of the prefix (`nick` in `nick!user@host`). A bare server-name prefix is
    /// returned whole; nil when the line has no prefix.
    public var nick: String? {
        guard let p = prefix, !p.isEmpty else { return nil }
        if let i = p.firstIndex(where: { $0 == "!" || $0 == "@" }) {
            return String(p[..<i])
        }
        return p
    }

    public init(tags: [String: String] = [:], prefix: String? = nil, command: String,
                params: [String] = [], trailing: String? = nil) {
        self.tags = tags
        self.prefix = prefix
        self.command = command
        self.params = params
        self.trailing = trailing
    }

    /// Parse one line (a trailing `\r` and/or `\n` is ignored). Returns nil for empty or
    /// command-less input.
    public static func parse(_ raw: String) -> IRCLine? {
        // Trim terminators on scalars: Swift treats "\r\n" as ONE Character, so `last == "\r"` misses it.
        var scalars = Substring(raw).unicodeScalars
        while let last = scalars.last, last == "\r" || last == "\n" { scalars = scalars.dropLast() }
        var s = Substring(scalars)

        func skipSpaces() { while s.first == " " { s = s.dropFirst() } }
        func takeToken() -> Substring {
            if let sp = s.firstIndex(of: " ") {
                let tok = s[..<sp]
                s = s[sp...]
                return tok
            }
            let tok = s
            s = s[s.endIndex...]
            return tok
        }

        var tags: [String: String] = [:]
        if s.first == "@" {
            s = s.dropFirst()
            let rawTags = takeToken()
            for part in rawTags.split(separator: ";", omittingEmptySubsequences: true) {
                if let eq = part.firstIndex(of: "=") {
                    tags[String(part[..<eq])] = unescapeTagValue(part[part.index(after: eq)...])
                } else {
                    tags[String(part)] = ""
                }
            }
            skipSpaces()
        }

        var prefix: String?
        if s.first == ":" {
            s = s.dropFirst()
            prefix = String(takeToken())
            skipSpaces()
        }

        let command = takeToken().uppercased()
        guard !command.isEmpty else { return nil }

        var params: [String] = []
        var trailing: String?
        while true {
            skipSpaces()
            if s.isEmpty { break }
            if s.first == ":" {
                let t = String(s.dropFirst())
                trailing = t
                params.append(t)
                break
            }
            params.append(String(takeToken()))
        }
        return IRCLine(tags: tags, prefix: prefix, command: command, params: params, trailing: trailing)
    }

    /// IRCv3 tag value unescaping: `\:`→`;`, `\s`→space, `\\`→`\`, `\r`, `\n`; other `\x`→`x`;
    /// a lone trailing backslash is dropped.
    static func unescapeTagValue(_ v: Substring) -> String {
        var out = ""
        var it = v.makeIterator()
        while let c = it.next() {
            guard c == "\\" else { out.append(c); continue }
            guard let n = it.next() else { break }
            switch n {
            case ":": out.append(";")
            case "s": out.append(" ")
            case "\\": out.append("\\")
            case "r": out.append("\r")
            case "n": out.append("\n")
            default: out.append(n)
            }
        }
        return out
    }

    /// Split one WebSocket text frame into IRC lines. A frame may carry one line with no
    /// terminator (text.ircv3.net style) or several lines ended by `\r\n` or `\n`.
    public static func splitFrame(_ frame: String) -> [String] {
        // Split on scalars, not Characters: Swift treats "\r\n" as ONE Character.
        frame.unicodeScalars
            .split(whereSeparator: { $0 == "\n" || $0 == "\r" })
            .map { String(String.UnicodeScalarView($0)) }
            .filter { !$0.isEmpty }
    }
}

/// Outgoing text rules for user-typed chat.
public enum IRCOutgoing {
    /// Max UTF-8 bytes of message text in one PRIVMSG. RFC 1459 caps a line at 512 bytes
    /// including CRLF, and the server prepends `:nick!user@host ` when relaying, so 400 leaves room.
    public static let maxTextBytes = 400

    /// Remove CR, LF and NUL (each would end or corrupt the IRC line), trim surrounding
    /// whitespace, and cut to `maxBytes` UTF-8 bytes on a Character boundary.
    public static func sanitize(_ text: String, maxBytes: Int = maxTextBytes) -> String {
        var cleaned = String(String.UnicodeScalarView(
            text.unicodeScalars.map { ($0 == "\r" || $0 == "\n") ? " " : $0 }.filter { $0 != "\u{0}" }))
        cleaned = cleaned.trimmingCharacters(in: .whitespaces)
        guard cleaned.utf8.count > maxBytes else { return cleaned }
        var out = ""
        var used = 0
        for ch in cleaned {
            let n = String(ch).utf8.count
            if used + n > maxBytes { break }
            out.append(ch)
            used += n
        }
        return out
    }
}

/// Tracks the `[thinking]` … `[/thinking]` block that sovereign-irc-bridge's `!llm` bot
/// (src/irc_llm_bot.py, `bridge_lines_to_irc`) sends with IRC_SHOW_THINKING=1, and the single
/// `(thinking: N line(s) hidden; …)` line it sends otherwise. The bot keeps its provenance
/// prefix, e.g. `[ClarkeYoursaTee (deepseek-r2-1.5b)] `, on the first reply line only.
public struct ThinkingTracker: Sendable {
    private var open: Set<String> = []

    public init() {}

    /// Text after an optional leading `[provenance] ` prefix.
    static func body(_ text: String) -> Substring {
        let t = Substring(text)
        if t.first == "[", let close = t.firstIndex(of: "]") {
            let afterClose = t.index(after: close)
            let tag = t[t.index(after: t.startIndex)..<close]
            // `[thinking]` / `[/thinking]` themselves are markers, not provenance.
            if tag != "thinking" && tag != "/thinking" && afterClose < t.endIndex && t[afterClose] == " " {
                return t[t.index(after: afterClose)...]
            }
        }
        return t
    }

    /// Classify one channel message from `sender`. Returns true when it should render dimmed
    /// (a thinking marker, a line inside a thinking block, or the "thinking hidden" summary).
    public mutating func isThinking(sender: String, text: String) -> Bool {
        let key = sender.lowercased()
        let b = Self.body(text).trimmingCharacters(in: .whitespaces)
        if b == "[thinking]" { open.insert(key); return true }
        if b == "[/thinking]" { open.remove(key); return true }
        if b.hasPrefix("(thinking:") && b.hasSuffix(")") { return true }
        return open.contains(key)
    }

    /// Forget all open blocks (call on reconnect).
    public mutating func reset() { open.removeAll() }
}
