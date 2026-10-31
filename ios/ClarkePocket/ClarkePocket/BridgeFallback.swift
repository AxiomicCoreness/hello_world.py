// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Chat fallback when the on-device model is unavailable (no model file yet, or it failed to load):
// ask the PC bridge's IRC bot (irc_llm_bot.py, ClarkeTutorBot) in a PRIVATE message over the
// existing IRCClient connection, and stream its "[LLM]" reply lines into the chat.
// OFF by default (a switch in the IRC tab): the question leaves the phone, and IRC is plaintext
// to the network's operators. Only the question is sent — never the system prompt or history.
// Nothing here opens a port or touches the PC; the phone only talks to the IRC network.

import Foundation
import Combine

@MainActor
final class BridgeFallback: ObservableObject {
    @Published var enabled = UserDefaults.standard.bool(forKey: "bridgeFallbackEnabled") {
        didSet { UserDefaults.standard.set(enabled, forKey: "bridgeFallbackEnabled") }
    }
    @Published private(set) var asking = false

    private weak var client: IRCClient?
    private var collector: BridgeReplyCollector?
    private var onText: (@MainActor (String) -> Void)?

    init(client: IRCClient) {
        self.client = client
        client.onDirectMessage = { [weak self] sender, text, isNotice in
            self?.receive(sender: sender, text: text, isNotice: isNotice)
        }
    }

    /// Switched on and IRC connected: chat can fall back to the PC bot.
    var isAvailable: Bool { enabled && (client?.isConnected ?? false) }

    /// Ask the PC bot. Returns the reply text (lines joined by "\n"), whether it was stopped, and
    /// an error for the chat to show. Cancel the calling Task to stop waiting.
    func ask(question: String, onText: @escaping @MainActor (String) -> Void) async -> (text: String, stopped: Bool, error: String?) {
        guard enabled else { return ("", false, "PC-bot fallback is off (IRC tab)") }
        guard let client, client.isConnected else { return ("", false, "no on-device model and IRC is not connected") }
        guard collector == nil else { return ("", false, "already waiting for the PC bot") }
        guard let line = BridgeRequest.pmText(question: question) else { return ("", false, "empty question") }
        collector = BridgeReplyCollector(startedAt: Date())
        self.onText = onText
        asking = true
        client.sendPrivate(line, to: BridgeRequest.botNick)
        var result: (String, Bool, String?) = ("", false, nil)
        while let c = collector {
            if Task.isCancelled { result = (c.text, true, nil); break }
            let st = c.state(now: Date())
            if st == .done {
                result = (c.text, false, c.text.isEmpty ? "PC bot: \(c.notice ?? "no answer")" : nil)
                break
            }
            if st == .timedOut {
                result = (c.text, false, "no answer from \(BridgeRequest.botNick) within \(Int(c.firstLineTimeout)) s — is the PC bot running?")
                break
            }
            try? await Task.sleep(nanoseconds: 250_000_000)
        }
        collector = nil
        self.onText = nil
        asking = false
        return result
    }

    private func receive(sender: String, text: String, isNotice: Bool) {
        guard var c = collector else { return }
        let piece = c.accept(sender: sender, text: text, isNotice: isNotice, now: Date())
        collector = c
        if let piece { onText?((c.lines.count > 1 ? "\n" : "") + piece) }
    }
}
