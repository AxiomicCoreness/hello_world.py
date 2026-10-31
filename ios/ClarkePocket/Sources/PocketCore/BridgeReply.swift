// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Fallback when the on-device model is unavailable: ask the PC bridge's IRC bot
// (sovereign-irc-bridge/src/irc_llm_bot.py, default nick ClarkeTutorBot) in a private message.
// Pure logic, no I/O, so it is unit-tested on Linux:
//   * the PM text sent to the bot ("!llm <question>", CR/LF/CTCP-free, ≤ 400 bytes);
//   * collecting the bot's reply: in a PM the bot sends "[LLM] <text>" lines with no "nick:" lead
//     and no end marker, so a reply is complete after `quietAfterLast` seconds without a new line,
//     or at once on the bot's "…(truncated)" line or a NOTICE (e.g. its rate-limit "slow down").
// Only the user's question goes to the bot: the PC bot keeps its own per-nick history and system
// prompt, and IRC is plaintext to the network's operators, so nothing else is sent.

import Foundation

public enum BridgeRequest {
    /// irc_llm_bot.py DEFAULT_NICK.
    public static let botNick = "ClarkeTutorBot"
    /// irc_llm_bot.py DEFAULT_LLM_TAG (every line the bot sends starts with it).
    public static let tag = "[LLM]"
    /// irc_llm_bot.py TRUNCATED_PM: always the bot's last line when it cut a PM reply short.
    public static let truncatedPM = "…(truncated)"

    /// The PM text for one question, or nil when nothing is left after sanitising.
    public static func pmText(question: String) -> String? {
        let flat = question.split(whereSeparator: { $0 == "\n" || $0 == "\r" || $0 == "\r\n" })
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }.joined(separator: " ")
            .replacingOccurrences(of: "\u{1}", with: "")   // no CTCP
        let q = IRCOutgoing.sanitize("!llm " + flat)
        return q.count > "!llm ".count ? q : nil
    }
}

public struct BridgeReplyCollector: Sendable {
    public enum State: Equatable, Sendable { case waiting, receiving, done, timedOut }

    public let botNick: String
    public let startedAt: Date
    /// No first line within this many seconds → give up (the PC bot may be off).
    public var firstLineTimeout: TimeInterval
    /// After the last line, this many quiet seconds end the reply.
    public var quietAfterLast: TimeInterval
    public private(set) var lines: [String] = []
    public private(set) var lastLineAt: Date?
    public private(set) var ended = false
    /// Set when the bot answered with a NOTICE (rate limit, error) instead of a reply.
    public private(set) var notice: String?

    public init(botNick: String = BridgeRequest.botNick, startedAt: Date,
                firstLineTimeout: TimeInterval = 180, quietAfterLast: TimeInterval = 4) {
        self.botNick = botNick
        self.startedAt = startedAt
        self.firstLineTimeout = firstLineTimeout
        self.quietAfterLast = quietAfterLast
    }

    /// Feed one direct message (PRIVMSG to us, or NOTICE). Returns the cleaned text that was
    /// added to the reply, or nil when the message is not part of it (another sender, after the
    /// end, the bot's "(thinking: … hidden)" note).
    public mutating func accept(sender: String, text: String, isNotice: Bool, now: Date) -> String? {
        guard !ended, sender.caseInsensitiveCompare(botNick) == .orderedSame else { return nil }
        var t = text.trimmingCharacters(in: .whitespaces)
        if t.hasPrefix(BridgeRequest.tag) { t = String(t.dropFirst(BridgeRequest.tag.count)).trimmingCharacters(in: .whitespaces) }
        if isNotice {
            notice = t
            ended = true
            lastLineAt = now
            return nil
        }
        if t.hasPrefix("(thinking:") { return nil }
        guard !t.isEmpty else { return nil }
        lines.append(t)
        lastLineAt = now
        if t == BridgeRequest.truncatedPM { ended = true }
        return t
    }

    public func state(now: Date) -> State {
        if ended { return .done }
        if let last = lastLineAt {
            return now.timeIntervalSince(last) >= quietAfterLast ? .done : .receiving
        }
        return now.timeIntervalSince(startedAt) >= firstLineTimeout ? .timedOut : .waiting
    }

    /// The reply so far, one bot line per text line.
    public var text: String { lines.joined(separator: "\n") }
}
