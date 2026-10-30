// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Optional: answer "!llm <question>" in the channel with the on-device model. OFF by default.
// Only while the app is open and in the foreground (iOS suspends it otherwise), only when the
// model is already loaded and idle, one question at a time, rate-limited (15 s global, 60 s per
// nick), ≤ 4 lines of ≤ 400 bytes, thinking never posted. The PC bot (PR #163) may answer
// !llm in the same channel too — turn this on only when that bot is not running.

import Foundation
import Combine

@MainActor
final class IRCResponder: ObservableObject {
    @Published var enabled = UserDefaults.standard.bool(forKey: "ircResponderEnabled") {
        didSet { UserDefaults.standard.set(enabled, forKey: "ircResponderEnabled") }
    }
    private var limiter = LLMRateLimiter()
    private let model: ModelStore
    private weak var client: IRCClient?

    init(model: ModelStore, client: IRCClient) {
        self.model = model
        self.client = client
        client.onChannelMessage = { [weak self] sender, channel, text in
            self?.consider(sender: sender, channel: channel, text: text)
        }
    }

    private func consider(sender: String, channel: String, text: String) {
        guard enabled, let client else { return }
        guard let trig = LLMReply.trigger(sender: sender, target: channel, text: text, ownNick: client.nickname) else { return }
        guard model.isLoaded, !model.busy else {
            client.note("!llm from \(sender) skipped: model \(model.isLoaded ? "busy" : "not loaded")")
            return
        }
        guard limiter.begin(nick: trig.asker, now: Date()) else {
            client.note("!llm from \(sender) skipped: rate limit")
            return
        }
        Task {
            defer { limiter.finish() }
            let system = "You are \(ModelPin.label) answering in an IRC channel. Reply in at most three short sentences, plain text."
            guard let r = await model.generate(system: system, history: [], user: trig.question,
                                               maxTokens: RuntimePolicy.maxIRCTokens, onText: { _ in }) else {
                client.note("!llm from \(sender) skipped: model busy")
                return
            }
            if let e = r.error { client.note("!llm failed: \(e)", error: true); return }
            if r.stopped { return }
            client.say(lines: LLMReply.lines(asker: trig.asker, rawReply: r.text), to: trig.channel)
        }
    }
}
