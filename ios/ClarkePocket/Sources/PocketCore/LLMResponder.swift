// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Rules for "Answer !llm with on-device model" (off by default). Pure logic, no I/O:
//   * trigger: a channel PRIVMSG whose text is "!llm <question>" (case-insensitive "!llm"),
//     never from our own nick, never a line that is itself an [LLM] reply (no bot ping-pong);
//   * rate limit: one answer at a time, ≥ `globalInterval` between answers, ≥ `perNickInterval`
//     per asker; a refused request is dropped silently (no "busy" spam in the channel);
//   * reply: the answer without its <think> block, CR/LF-free, cut into ≤ `maxLines` IRC lines
//     each "[LLM] " + text within 400 bytes; the first line addresses the asker ("nick: …").

import Foundation

public struct LLMTrigger: Equatable, Sendable {
    public var asker: String
    public var channel: String
    public var question: String
}

public enum LLMReply {
    public static let tag = "[LLM] "
    public static let maxLines = 4

    /// Parse a channel message. nil when it is not a request this phone should consider.
    public static func trigger(sender: String, target: String, text: String, ownNick: String) -> LLMTrigger? {
        guard target.first.map({ "#&+!".contains($0) }) == true else { return nil }   // channel only
        guard sender.caseInsensitiveCompare(ownNick) != .orderedSame else { return nil }
        let t = text.trimmingCharacters(in: .whitespaces)
        guard !t.hasPrefix("[LLM]") else { return nil }
        guard t.count > 4, t.prefix(4).lowercased() == "!llm",
              let fifth = t.dropFirst(4).first, fifth == " " || fifth == "\t" else { return nil }
        let q = IRCOutgoing.sanitize(String(t.dropFirst(5)))
        guard !q.isEmpty else { return nil }
        return LLMTrigger(asker: sender, channel: target, question: q)
    }

    /// IRC lines for a raw model reply (thinking removed). Never empty.
    public static func lines(asker: String, rawReply: String,
                             maxBytes: Int = IRCOutgoing.maxTextBytes, maxLines: Int = maxLines) -> [String] {
        var answer = MarkdownMath.splitThinking(rawReply).answer
        if answer.isEmpty { answer = "(no answer within the token limit)" }
        // Flatten: paragraphs → " ", CR/LF/NUL/CTCP gone.
        let flat = answer.split(whereSeparator: { $0 == "\n" || $0 == "\r\n" || $0 == "\r" })
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }.joined(separator: " ")
        let words = IRCCommand.cleanText(flat, maxBytes: Int.max).split(separator: " ", omittingEmptySubsequences: true)
        let budget = maxBytes - tag.utf8.count
        var out: [String] = []
        var cur = "\(asker):"
        func push() { out.append(tag + cur) }
        var truncated = false
        for w in words {
            var word = String(w)
            if word.utf8.count > budget { word = IRCOutgoing.sanitize(word, maxBytes: budget) }
            if (cur + " " + word).utf8.count <= budget {
                cur += cur.isEmpty ? word : " " + word
            } else {
                push()
                if out.count == maxLines { truncated = true; break }
                cur = word
            }
        }
        if !truncated && !cur.isEmpty { push() }
        if truncated || out.count > maxLines {
            out = Array(out.prefix(maxLines))
            var last = out[maxLines - 1]
            while last.utf8.count + " …".utf8.count > maxBytes, !last.isEmpty { last.removeLast() }
            out[maxLines - 1] = last + " …"
        }
        return out
    }
}

/// Clock-injected rate limiter (tests pass their own `now`).
public struct LLMRateLimiter: Sendable {
    public var globalInterval: TimeInterval
    public var perNickInterval: TimeInterval
    private var lastAny: Date?
    private var lastByNick: [String: Date] = [:]
    public private(set) var busy = false

    public init(globalInterval: TimeInterval = 15, perNickInterval: TimeInterval = 60) {
        self.globalInterval = globalInterval
        self.perNickInterval = perNickInterval
    }

    /// Ask to start an answer for `nick`. True → caller must call `finish()` when done.
    public mutating func begin(nick: String, now: Date) -> Bool {
        let key = nick.lowercased()
        if busy { return false }
        if let l = lastAny, now.timeIntervalSince(l) < globalInterval { return false }
        if let l = lastByNick[key], now.timeIntervalSince(l) < perNickInterval { return false }
        busy = true
        lastAny = now
        lastByNick[key] = now
        if lastByNick.count > 256 {   // bounded memory in a busy channel
            lastByNick = lastByNick.filter { now.timeIntervalSince($0.value) < perNickInterval }
        }
        return true
    }

    public mutating func finish() { busy = false }
}
