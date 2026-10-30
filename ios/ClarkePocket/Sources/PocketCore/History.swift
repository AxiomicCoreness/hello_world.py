// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Local chat history as JSONL, row for row the shape sovereign-irc-bridge writes since PR #166
// (src/llm_chat.py `append_history`):
//
//   {"role": "user", "content": "…", "session": "pocket", "ts": "2026-10-30T17:40:00-04:00"}
//   {"role": "assistant", "content": "…", "format": "markdown", "thinking": "…", "session": "pocket", "ts": "…"}
//
// Keys in that order, `", "` / `": "` separators and non-ASCII written as-is: byte-identical to
// Python's `json.dumps(row, ensure_ascii=False)`, so a file from the phone can be appended to or
// diffed against the bridge's llm_history.jsonl. `thinking` appears only when non-empty.
// `ts` is ISO 8601 with the phone's UTC offset (e.g. -04:00 in New York).

import Foundation

public struct HistoryRow: Equatable, Sendable {
    public enum Role: String, Sendable { case user, assistant }

    public var role: Role
    public var content: String
    /// "markdown" on assistant rows written by this app; nil on user rows and legacy rows.
    public var format: String?
    public var thinking: String?
    public var session: String
    public var ts: String

    public init(role: Role, content: String, format: String? = nil, thinking: String? = nil,
                session: String, ts: String) {
        self.role = role
        self.content = content
        self.format = format
        self.thinking = thinking
        self.session = session
        self.ts = ts
    }
}

public enum History {
    public static let defaultSession = "default"
    /// The app's own session name (bridge rule: `[A-Za-z0-9_-]{1,64}`).
    public static let appSession = "pocket"

    /// Bridge `normalize_session`: `[A-Za-z0-9_-]{1,64}` after trimming, else "default".
    public static func normalizeSession(_ raw: String?) -> String {
        let s = (raw ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard (1...64).contains(s.count),
              s.unicodeScalars.allSatisfy({ ("a"..."z").contains($0) || ("A"..."Z").contains($0)
                  || ("0"..."9").contains($0) || $0 == "_" || $0 == "-" })
        else { return defaultSession }
        return s
    }

    /// ISO 8601 with seconds and the given zone's offset (`2026-10-30T17:40:00-04:00`; `Z` is never used).
    public static func timestamp(_ date: Date = Date(), timeZone: TimeZone = .current) -> String {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = timeZone
        let c = cal.dateComponents([.year, .month, .day, .hour, .minute, .second], from: date)
        let off = timeZone.secondsFromGMT(for: date)
        let sign = off < 0 ? "-" : "+"
        let a = abs(off)
        return String(format: "%04d-%02d-%02dT%02d:%02d:%02d%@%02d:%02d",
                      c.year ?? 0, c.month ?? 0, c.day ?? 0, c.hour ?? 0, c.minute ?? 0, c.second ?? 0,
                      sign, a / 3600, (a % 3600) / 60)
    }

    /// One user/assistant pair, as the bridge writes it after a reply. The raw model output is
    /// split into answer + thinking and math is normalised exactly like `markdown_entry`.
    public static func pair(user: String, rawReply: String, session: String = appSession,
                            date: Date = Date(), timeZone: TimeZone = .current) -> [HistoryRow] {
        let ts = timestamp(date, timeZone: timeZone)
        let s = normalizeSession(session)
        let (answer, thinking) = MarkdownMath.splitThinking(rawReply)
        let entry = MarkdownMath.markdownEntry(answer: answer, thinking: thinking)
        return [
            HistoryRow(role: .user, content: user, session: s, ts: ts),
            HistoryRow(role: .assistant, content: entry.content, format: MarkdownMath.formatMarkdown,
                       thinking: entry.thinking, session: s, ts: ts),
        ]
    }

    // MARK: Encoding

    /// Python `json.dumps(s, ensure_ascii=False)` for one string.
    public static func jsonString(_ s: String) -> String {
        var out = "\""
        for u in s.unicodeScalars {
            switch u {
            case "\"": out += "\\\""
            case "\\": out += "\\\\"
            case "\n": out += "\\n"
            case "\r": out += "\\r"
            case "\t": out += "\\t"
            case "\u{08}": out += "\\b"
            case "\u{0C}": out += "\\f"
            default:
                if u.value < 0x20 {
                    out += String(format: "\\u%04x", u.value)
                } else {
                    out.unicodeScalars.append(u)
                }
            }
        }
        return out + "\""
    }

    /// One JSONL line (no trailing newline).
    public static func encode(_ r: HistoryRow) -> String {
        var fields: [(String, String)] = [("role", r.role.rawValue), ("content", r.content)]
        if r.role == .assistant, let f = r.format {
            fields.append(("format", f))
            if let t = r.thinking, !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                fields.append(("thinking", t))
            }
        }
        fields.append(("session", r.session))
        fields.append(("ts", r.ts))
        return "{" + fields.map { jsonString($0.0) + ": " + jsonString($0.1) }.joined(separator: ", ") + "}"
    }

    /// Parse one JSONL line. Bad JSON, unknown roles or non-string content → nil (skipped, like
    /// the bridge). Legacy rows (no `format`) keep `format == nil`; `thinking` is only read from
    /// markdown rows (`read_entry`). Rows without a valid session count as "default".
    public static func decode(_ line: String) -> HistoryRow? {
        guard let data = line.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let roleRaw = obj["role"] as? String, let role = HistoryRow.Role(rawValue: roleRaw),
              let content = obj["content"] as? String
        else { return nil }
        let format = (obj["format"] as? String).flatMap { ["markdown", "plain"].contains($0) ? $0 : nil }
        var thinking: String?
        if format == "markdown", let t = obj["thinking"] as? String,
           !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { thinking = t }
        let session = normalizeSession(obj["session"] as? String)
        return HistoryRow(role: role, content: content, format: format, thinking: thinking,
                          session: session, ts: (obj["ts"] as? String) ?? "")
    }

    /// Lines → rows, skipping blanks and anything unreadable.
    public static func decodeAll(_ text: String) -> [HistoryRow] {
        text.split(whereSeparator: { $0 == "\n" || $0 == "\r\n" }).compactMap { decode(String($0)) }
    }
}

/// Append-only JSONL file (Application Support on the phone). Every write is one `write` of
/// whole lines followed by `synchronize()` (fsync), like the bridge. Never throws to callers.
public final class HistoryFile: @unchecked Sendable {
    public let url: URL
    private let lock = NSLock()

    public init(url: URL) { self.url = url }

    @discardableResult
    public func append(_ rows: [HistoryRow]) -> Bool {
        lock.lock(); defer { lock.unlock() }
        let payload = rows.map { History.encode($0) + "\n" }.joined()
        do {
            try FileManager.default.createDirectory(at: url.deletingLastPathComponent(),
                                                    withIntermediateDirectories: true)
            if !FileManager.default.fileExists(atPath: url.path) {
                _ = FileManager.default.createFile(atPath: url.path, contents: nil)
            }
            let h = try FileHandle(forWritingTo: url)
            defer { try? h.close() }
            try h.seekToEnd()
            try h.write(contentsOf: Data(payload.utf8))
            try h.synchronize()
            return true
        } catch {
            return false
        }
    }

    public func readAll() -> [HistoryRow] {
        lock.lock(); defer { lock.unlock() }
        guard let data = try? Data(contentsOf: url) else { return [] }
        return History.decodeAll(String(decoding: data, as: UTF8.self))
    }

    /// Move the file aside as `<name>.reset-<session>-<ts>` (like `/llm reset`, which archives).
    @discardableResult
    public func archive(now: Date = Date()) -> URL? {
        lock.lock(); defer { lock.unlock() }
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        let stamp = History.timestamp(now).replacingOccurrences(of: ":", with: "")
        let dest = url.deletingLastPathComponent()
            .appendingPathComponent(url.lastPathComponent + ".reset-\(History.appSession)-\(stamp)")
        do { try FileManager.default.moveItem(at: url, to: dest); return dest } catch { return nil }
    }
}
