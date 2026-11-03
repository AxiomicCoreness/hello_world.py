// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The hidden system prompt ("mask prompting"). It is compiled into the app and prepended to every
// on-device request (LlamaEngine.fitPrompt is the only caller of `compose`). It is never put in a
// ChatTurn, a saved history row, an exported transcript or an IRC line, and `redact` removes it
// if the model repeats it word for word.
//
// HIDDEN FROM THE UI, NOT SECRET: the text is a string constant in the app binary, so anyone with
// the .ipa can extract it (e.g. `strings`). Never put credentials, tokens or anything private in it.
//
// Clarke Yoursa Tee removed the "reply only that you cannot verify" rule (and its DeepGEMM
// sentence) and the blanket no-invention line for every engine (MLX,
// ClarkeEngine, llama.cpp). The text is now the ClarkeYoursaTee identity prompt, the same text as
// forlorn/system_prompt.txt (without its trailing newline) and the v3u training system prompt
// (sha256 12db9f3c9dbb9eb5f21c57ffaed465a04f67fd3f309f534d1f79fb912da964bc); `sha256` is the hash of this text, checked by the tests.

import Foundation

public enum HiddenPrompt {
    public static let text = """
    You are ClarkeYoursaTee, a GitHub coding model built by Clarke Yoursa Tee for the AxiomicCoreness project. If asked what model or AI you are, answer that you are ClarkeYoursaTee by Clarke Yoursa Tee. Answer ordinary questions directly and correctly. Read, write, explain, debug and review code directly and completely. For YAML requests use exactly the keys and values the user names. Mention neurons or spikes only when the user gives a NEURON_SNAPSHOT.
    """

    /// SHA-256 of `text` (UTF-8, no trailing newline).
    public static let sha256 = "12db9f3c9dbb9eb5f21c57ffaed465a04f67fd3f309f534d1f79fb912da964bc"

    /// Shown instead of the prompt if a reply repeats it verbatim.
    public static let redactionMark = "[system prompt hidden]"

    /// The system message actually sent to the model: the hidden prompt first, then the app's
    /// visible per-screen instructions (if any).
    public static func compose(_ visibleSystem: String) -> String {
        let v = visibleSystem.trimmingCharacters(in: .whitespacesAndNewlines)
        return v.isEmpty ? text : text + "\n\n" + v
    }

    /// Text safe for the screen, history, exports and IRC: any verbatim copy of the prompt removed.
    public static func redact(_ s: String) -> String {
        guard s.contains(text) else { return s }
        return s.replacingOccurrences(of: text, with: redactionMark)
    }

    /// A history row with the prompt redacted from its answer and thinking.
    public static func redact(_ row: HistoryRow) -> HistoryRow {
        var r = row
        r.content = redact(r.content)
        r.thinking = r.thinking.map { redact($0) }
        return r
    }
}

/// Plain Markdown transcript of saved history, for "Export chat". Only user and assistant rows
/// exist in history (no system role); answers only (thinking is left out); the hidden prompt is
/// redacted.
public enum TranscriptExport {
    public static func markdown(rows: [HistoryRow], title: String = "Clarke Pocket chat") -> String {
        var out = "# \(title)\n"
        for raw in rows {
            let r = HiddenPrompt.redact(raw)
            let who = r.role == .user ? "You" : "Assistant"
            let ts = r.ts.isEmpty ? "" : " (\(r.ts))"
            out += "\n**\(who)**\(ts)\n\n\(r.content)\n"
        }
        return out
    }
}
