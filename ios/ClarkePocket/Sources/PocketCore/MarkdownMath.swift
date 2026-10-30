// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Swift port of sovereign-irc-bridge/src/llm_markdown.py (PR #166, feat/llm-markdown-latex @ aed929c7):
//   * `MarkdownMath.normalizeMath` — math delimiters → inline `\( … \)` / display `$$ … $$`,
//     code spans and fenced code blocks copied byte for byte (same regex, same order).
//   * `MarkdownMath.splitThinking` — `<think>…</think>` reasoning → (answer, thinking).
// Plus what the app needs on top: a streaming view of a reply (is the think block still open?)
// and a segmenter that cuts a reply into code / display math / prose-with-inline-math for display.
// Only difference from Python: lines are split on "\n" (Python's splitlines also splits on rare
// separators such as U+2028); replies from the model use "\n".

import Foundation

public enum MarkdownMath {
    public static let formatMarkdown = "markdown"

    // A fence opener: up to 3 spaces, then >=3 backticks or >=3 tildes.
    private static let fenceRE = try! NSRegularExpression(pattern: "^( {0,3})(`{3,}|~{3,})")

    // Prose math, tried left to right at each position. Order matters: $$ before $.
    private static let mathRE = try! NSRegularExpression(
        pattern: #"(?<esc>\\\$)"#
            + #"|\$\$(?<dd>.+?)\$\$"#
            + #"|\\\[(?<bd>.+?)\\\]"#
            + #"|\\\((?<bi>.+?)\\\)"#
            + #"|(?<![\\$\w])\$(?=[^\s$])(?<di>[^$\n]*?[^\s\\$])\$(?![\w$])"#,
        options: [.dotMatchesLineSeparators])

    /// Lines with their terminators kept (Python `splitlines(keepends=True)` for "\n" / "\r\n").
    static func linesKeepingEnds(_ text: String) -> [String] {
        var out: [String] = []
        var cur = ""
        for ch in text {
            cur.append(ch)
            if ch == "\n" || ch == "\r\n" {
                out.append(cur)
                cur = ""
            }
        }
        if !cur.isEmpty { out.append(cur) }
        return out
    }

    /// [(isCode, chunk)] for fenced code blocks vs everything else (line based).
    public static func splitFences(_ text: String) -> [(isCode: Bool, text: String)] {
        var out: [(Bool, String)] = []
        var buf: [String] = []
        var fence: String?
        for line in linesKeepingEnds(text) {
            let ns = line as NSString
            let m = fenceRE.firstMatch(in: line, range: NSRange(location: 0, length: ns.length))
            if fence == nil {
                if let m {
                    if !buf.isEmpty { out.append((false, buf.joined())) }
                    buf = [line]
                    fence = ns.substring(with: m.range(at: 2))
                } else {
                    buf.append(line)
                }
            } else {
                buf.append(line)
                let stripped = line.trimmingCharacters(in: .whitespacesAndNewlines)
                if m != nil, let f = fence, let f0 = f.first, !stripped.isEmpty,
                   Set(stripped) == [f0], stripped.count >= f.count {
                    out.append((true, buf.joined()))
                    buf = []
                    fence = nil
                }
            }
        }
        if !buf.isEmpty { out.append((fence != nil, buf.joined())) }  // an unclosed fence stays code
        return out
    }

    /// [(isCode, chunk)] for inline code spans (a backtick run of n closes on a run of n).
    public static func splitCodeSpans(_ prose: String) -> [(isCode: Bool, text: String)] {
        let chars = Array(prose)
        var out: [(Bool, String)] = []
        var i = 0, start = 0
        let n = chars.count
        while i < n {
            if chars[i] != "`" { i += 1; continue }
            var j = i
            while j < n && chars[j] == "`" { j += 1 }
            let runLen = j - i
            // Find a run of exactly runLen backticks at or after j.
            var k = j
            var closeEnd: Int?
            while k < n {
                if chars[k] == "`" {
                    var e = k
                    while e < n && chars[e] == "`" { e += 1 }
                    if e - k == runLen { closeEnd = e; break }
                    k = e
                } else {
                    k += 1
                }
            }
            guard let end = closeEnd else { i = j; continue }  // no closer: backticks are literal
            if i > start { out.append((false, String(chars[start..<i]))) }
            out.append((true, String(chars[i..<end])))
            i = end
            start = end
        }
        if start < n { out.append((false, String(chars[start..<n]))) }
        return out
    }

    static func normProse(_ s: String) -> String {
        let ns = s as NSString
        var out = ""
        var last = 0
        for m in mathRE.matches(in: s, range: NSRange(location: 0, length: ns.length)) {
            out += ns.substring(with: NSRange(location: last, length: m.range.location - last))
            let whole = ns.substring(with: m.range)
            last = m.range.location + m.range.length
            if m.range(withName: "esc").location != NSNotFound { out += whole; continue }
            var replaced: String?
            for (g, lo, hi) in [("dd", "$$", "$$"), ("bd", "$$", "$$"), ("bi", "\\(", "\\)"), ("di", "\\(", "\\)")] {
                let r = m.range(withName: g)
                guard r.location != NSNotFound else { continue }
                let body = ns.substring(with: r).trimmingCharacters(in: .whitespacesAndNewlines)
                replaced = body.isEmpty ? whole : lo + body + hi
                break
            }
            out += replaced ?? whole
        }
        out += ns.substring(from: last)
        return out
    }

    /// Rewrite math delimiters in Markdown prose to `\( … \)` / `$$ … $$` (fixed point).
    public static func normalizeMath(_ text: String) -> String {
        guard !text.isEmpty else { return text }
        var parts: [String] = []
        for (isCode, chunk) in splitFences(text) {
            if isCode { parts.append(chunk); continue }
            for (spanCode, piece) in splitCodeSpans(chunk) {
                parts.append(spanCode ? piece : normProse(piece))
            }
        }
        return parts.joined()
    }

    private static let thinkBlockRE = try! NSRegularExpression(
        pattern: "<think>(.*?)</think>", options: [.dotMatchesLineSeparators])

    /// Pull `<think>…</think>` reasoning out of a reply → (answer, thinking). Handles a reply whose
    /// prompt already opened `<think>` (text before a lone `</think>` is reasoning) and an unclosed
    /// `<think>` (the rest is reasoning). Same as Python `split_thinking`.
    public static func splitThinking(_ reply: String) -> (answer: String, thinking: String) {
        var text = reply
        var thoughts: [String] = []
        if let close = text.range(of: "</think>") {
            let head = text[..<close.lowerBound]
            if !head.contains("<think>") {
                thoughts.append(String(head))
                text = String(text[close.upperBound...])
            }
        }
        let ns = text as NSString
        var rebuilt = ""
        var last = 0
        for m in thinkBlockRE.matches(in: text, range: NSRange(location: 0, length: ns.length)) {
            rebuilt += ns.substring(with: NSRange(location: last, length: m.range.location - last))
            thoughts.append(ns.substring(with: m.range(at: 1)))
            last = m.range.location + m.range.length
        }
        rebuilt += ns.substring(from: last)
        text = rebuilt
        if let open = text.range(of: "<think>") {
            thoughts.append(String(text[open.upperBound...]))
            text = String(text[..<open.lowerBound])
        }
        let thinking = thoughts.map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }.joined(separator: "\n\n")
        return (text.trimmingCharacters(in: .whitespacesAndNewlines), thinking)
    }

    /// While streaming: true when the reply has an opened `<think>` that is not closed yet.
    public static func thinkingOpen(_ partial: String) -> Bool {
        guard let open = partial.range(of: "<think>", options: .backwards) else { return false }
        return partial.range(of: "</think>", range: open.upperBound..<partial.endIndex) == nil
    }

    /// Saved-reply fields for an assistant row (Python `markdown_entry`).
    public static func markdownEntry(answer: String, thinking: String = "") -> (content: String, thinking: String?) {
        var content = normalizeMath(answer.trimmingCharacters(in: .whitespacesAndNewlines))
        if content.isEmpty { content = "(empty reply)" }
        let t = normalizeMath(thinking.trimmingCharacters(in: .whitespacesAndNewlines))
        return (content, t.isEmpty ? nil : t)
    }
}

// MARK: - Display segmentation

/// One run inside a prose block: Markdown text (bold, italics, `code`, links) or inline math.
public enum InlineRun: Equatable, Sendable {
    case markdown(String)
    case math(String)
}

/// A displayable block of a reply.
public enum ReplyBlock: Equatable, Sendable {
    case prose([InlineRun])
    case displayMath(String)
    case code(language: String, body: String)
}

public enum ReplySegmenter {
    private static let mathRunRE = try! NSRegularExpression(
        pattern: #"\$\$(.+?)\$\$|\\\((.+?)\\\)"#, options: [.dotMatchesLineSeparators])

    /// Cut a (normalised) Markdown reply into blocks. Math inside code is never extracted.
    public static func segment(_ text: String) -> [ReplyBlock] {
        var blocks: [ReplyBlock] = []
        var runs: [InlineRun] = []

        func pushMarkdown(_ s: String) {
            guard !s.isEmpty else { return }
            if case .markdown(let prev)? = runs.last {
                runs[runs.count - 1] = .markdown(prev + s)
            } else {
                runs.append(.markdown(s))
            }
        }
        func flushProse() {
            // Drop runs that are only whitespace (e.g. the newline around a display formula).
            let meaningful = runs.contains {
                if case .markdown(let s) = $0 { return !s.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
                return true
            }
            if meaningful {
                var trimmed = runs
                if case .markdown(let s)? = trimmed.first {
                    trimmed[0] = .markdown(String(s.drop(while: { $0 == "\n" || $0 == "\r\n" })))
                }
                if case .markdown(let s)? = trimmed.last {
                    var t = s
                    while let l = t.last, l == "\n" || l == "\r\n" || l == " " { t.removeLast() }
                    trimmed[trimmed.count - 1] = .markdown(t)
                }
                blocks.append(.prose(trimmed.filter { $0 != .markdown("") }))
            }
            runs = []
        }

        for (isCode, chunk) in MarkdownMath.splitFences(text) {
            if isCode {
                flushProse()
                var lines = MarkdownMath.linesKeepingEnds(chunk)
                let opener = lines.isEmpty ? "" : lines.removeFirst()
                let lang = opener.trimmingCharacters(in: .whitespacesAndNewlines)
                    .trimmingCharacters(in: CharacterSet(charactersIn: "`~")).trimmingCharacters(in: .whitespaces)
                if let last = lines.last {
                    let s = last.trimmingCharacters(in: .whitespacesAndNewlines)
                    if !s.isEmpty, let f = s.first, (f == "`" || f == "~"), Set(s) == [f] { lines.removeLast() }
                }
                var body = lines.joined()
                while body.hasSuffix("\n") { body.removeLast() }
                blocks.append(.code(language: lang, body: body))
                continue
            }
            for (spanCode, piece) in MarkdownMath.splitCodeSpans(chunk) {
                if spanCode { pushMarkdown(piece); continue }
                let ns = piece as NSString
                var last = 0
                for m in mathRunRE.matches(in: piece, range: NSRange(location: 0, length: ns.length)) {
                    pushMarkdown(ns.substring(with: NSRange(location: last, length: m.range.location - last)))
                    last = m.range.location + m.range.length
                    if m.range(at: 1).location != NSNotFound {
                        flushProse()
                        blocks.append(.displayMath(ns.substring(with: m.range(at: 1))
                            .trimmingCharacters(in: .whitespacesAndNewlines)))
                    } else {
                        runs.append(.math(ns.substring(with: m.range(at: 2))
                            .trimmingCharacters(in: .whitespacesAndNewlines)))
                    }
                }
                pushMarkdown(ns.substring(from: last))
            }
        }
        flushProse()
        return blocks
    }
}
