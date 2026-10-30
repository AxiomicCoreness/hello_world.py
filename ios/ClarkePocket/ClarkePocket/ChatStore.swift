// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The on-device chat: what is on screen, and the saved history. Saved replies use the bridge's
// format (PR #166): one JSONL row per turn, assistant rows `"format": "markdown"` with LaTeX math
// normalised and the reasoning in a separate `thinking` field — never fed back to the model.
// File: Application Support/llm_history.jsonl, session "pocket", timestamps with the phone's offset.

import Foundation
import SwiftUI

struct ChatTurn: Identifiable, Equatable {
    enum Role: Equatable { case user, assistant, note }
    let id = UUID()
    var role: Role
    /// User text, or the assistant's raw streamed text (may contain <think>…</think>).
    var text: String
    var streaming = false
    var stopped = false

    var answer: String { MarkdownMath.normalizeMath(MarkdownMath.splitThinking(text).answer) }
    var thinking: String { MarkdownMath.splitThinking(text).thinking }
    var isThinkingNow: Bool { streaming && MarkdownMath.thinkingOpen(text) }
}

@MainActor
final class ChatStore: ObservableObject {
    @Published private(set) var turns: [ChatTurn] = []
    @Published private(set) var generating = false

    static let systemPrompt = """
    You are \(ModelPin.label), a helpful assistant running entirely on the user's iPhone. \
    Answer concisely. Use Markdown, and write math in LaTeX with \\( \\) or \\[ \\].
    """
    /// History rows used as context (the prompt window trims further to fit 2048 tokens).
    static let maxContextRows = 20

    let history: HistoryFile
    private let model: ModelStore

    init(model: ModelStore) {
        self.model = model
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: base, withIntermediateDirectories: true)
        history = HistoryFile(url: base.appendingPathComponent("llm_history.jsonl"))
        loadSaved()
    }

    private func loadSaved() {
        turns = history.readAll().suffix(200).map { row in
            switch row.role {
            case .user: return ChatTurn(role: .user, text: row.content)
            case .assistant:
                // Show saved thinking the same way as live thinking.
                let t = row.thinking.map { "<think>\($0)</think>\n\n" } ?? ""
                return ChatTurn(role: .assistant, text: t + row.content)
            }
        }
    }

    func send(_ typed: String) {
        let user = typed.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !user.isEmpty, !generating else { return }
        guard !model.busy else {
            turns.append(ChatTurn(role: .note, text: "the model is answering IRC right now — try again in a moment"))
            return
        }
        let context = PromptWindow.turns(from: Array(history.readAll().suffix(Self.maxContextRows)))
        turns.append(ChatTurn(role: .user, text: user))
        turns.append(ChatTurn(role: .assistant, text: "", streaming: true))
        let idx = turns.count - 1
        generating = true
        Task {
            let result = await model.generate(system: Self.systemPrompt, history: context, user: user,
                                              maxTokens: RuntimePolicy.maxChatTokens) { [weak self] piece in
                guard let self, idx < self.turns.count else { return }
                self.turns[idx].text += piece
            }
            generating = false
            guard idx < turns.count else { return }
            turns[idx].streaming = false
            guard let r = result else {
                turns.remove(at: idx)
                let why: String
                if let w = model.memoryWarning { why = w }
                else if case .failed(let e) = model.engineState { why = e }
                else { why = "the model is not ready — open the Model tab" }
                turns.append(ChatTurn(role: .note, text: why))
                return
            }
            if let e = r.error { turns.append(ChatTurn(role: .note, text: "error: \(e)")) }
            turns[idx].stopped = r.stopped
            if !r.text.isEmpty {
                history.append(History.pair(user: user, rawReply: r.text))
            }
        }
    }

    func stop() { model.cancelCurrent() }

    /// Like the bridge's `/llm reset`: archive the file, start fresh.
    func reset() {
        guard !generating else { return }
        history.archive()
        turns = [ChatTurn(role: .note, text: "history archived — new conversation")]
    }
}
