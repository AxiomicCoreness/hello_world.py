// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Direct Libera.Chat client over WebSocket. The phone talks to Libera itself; nothing on the
// user's PC is exposed (no open port, no tunnel, no all-interfaces bind). The !llm bot
// (sovereign-irc-bridge/src/irc_llm_bot.py) sits in the same channel and answers there.
//
// Lifecycle: connect only while the app is in the foreground (ChatView drives this from
// scenePhase). A dropped socket reconnects with exponential backoff capped at 60 s. Nothing in
// this file terminates the app; failures only change `status` and schedule a retry.

import Foundation
#if canImport(Combine)
import Combine                // ObservableObject / @Published
#endif
#if canImport(FoundationNetworking)
import FoundationNetworking   // Linux toolchain only (used for the offline harness); a no-op on iOS
#endif

enum IRCConfig {
    /// Libera's own web gateway — the `server.url` in https://web.libera.chat/gamja/config.json.
    static let gatewayURL = URL(string: "wss://web.libera.chat/webirc/websocket/")!
    static let channel = "#axiomiccoreness"
    static let nickBase = "Clarke_iOS_"
    /// Backoff after a failed or dropped connection: 1, 2, 4 … seconds, never more than this.
    static let maxBackoffSeconds: Double = 60
    /// Keep at most this many lines in memory.
    static let maxHistory = 500

    static func randomNick() -> String { "\(nickBase)\(Int.random(in: 1000...9999))" }
}

/// One rendered chat row. `id` is a fresh UUID so identical texts ("ok", "ok") are separate rows.
struct ChatMessage: Identifiable, Equatable {
    enum Kind: Equatable { case own, peer, system, error }

    let id = UUID()
    let date = Date()
    let kind: Kind
    let sender: String?
    let text: String
    /// Part of the bot's `[thinking]` block (rendered dimmed, like a `.locked` control on the page).
    let thinking: Bool

    init(kind: Kind, sender: String? = nil, text: String, thinking: Bool = false) {
        self.kind = kind
        self.sender = sender
        self.text = text
        self.thinking = thinking
    }
}

@MainActor
final class LiberaIRCClient: ObservableObject {
    enum Status: Equatable { case offline, connecting, connected }

    @Published private(set) var messages: [ChatMessage] = []
    @Published private(set) var status: Status = .offline
    @Published private(set) var nickname = IRCConfig.randomNick()

    /// Kept for the view's dot/label; true only after the server's 001 welcome.
    var isConnected: Bool { status == .connected }

    private let session = URLSession(configuration: .default)
    private var task: URLSessionWebSocketTask?
    private var receiveLoop: Task<Void, Never>?
    private var reconnectTask: Task<Void, Never>?
    private var sendChain: Task<Void, Never>?
    /// Bumped on every (re)connect so callbacks from an old socket are ignored.
    private var generation = 0
    private var failures = 0
    private var registered = false
    /// False while the app is backgrounded: no reconnects then.
    private var wantsConnection = false
    private var thinking = ThinkingTracker()

    // MARK: Lifecycle

    /// Foreground: connect now (if not already) and allow automatic reconnects.
    func start() {
        wantsConnection = true
        if status == .offline { connect(resetBackoff: true) }
    }

    /// Background / view gone: say goodbye, close the socket, cancel any pending retry.
    func stop() {
        wantsConnection = false
        reconnectTask?.cancel()
        reconnectTask = nil
        if task != nil, registered { sendRaw("QUIT :backgrounded") }
        teardown(closeCode: .goingAway)
        status = .offline
    }

    /// "Reconnect" button: drop whatever is there and dial again immediately.
    func reconnectNow() {
        wantsConnection = true
        reconnectTask?.cancel()
        reconnectTask = nil
        connect(resetBackoff: true)
    }

    private func connect(resetBackoff: Bool) {
        if resetBackoff { failures = 0 }
        teardown(closeCode: .goingAway)   // always cancel the old task first (bumps generation)
        let gen = generation
        registered = false
        thinking.reset()
        status = .connecting
        append(.system, text: "connecting to \(IRCConfig.gatewayURL.absoluteString) …")

        let t = session.webSocketTask(with: IRCConfig.gatewayURL)
        task = t
        t.resume()
        // Sends before the socket opens are queued by URLSession and go out once it opens.
        sendRaw("NICK \(nickname)")
        sendRaw("USER \(nickname) 0 * :AxiomicCoreness iOS")

        receiveLoop = Task { [weak self] in
            while !Task.isCancelled {
                do {
                    let frame = try await t.receive()
                    guard let self, self.generation == gen else { return }
                    switch frame {
                    case .string(let text): self.handleFrame(text)
                    case .data(let data): self.handleFrame(String(decoding: data, as: UTF8.self))
                    @unknown default: break
                    }
                } catch {
                    guard let self, self.generation == gen else { return }
                    self.connectionLost("receive failed: \(error.localizedDescription)")
                    return
                }
            }
        }
    }

    private func teardown(closeCode: URLSessionWebSocketTask.CloseCode) {
        generation += 1                  // late callbacks from the old socket are now ignored
        receiveLoop?.cancel()
        receiveLoop = nil
        task?.cancel(with: closeCode, reason: nil)
        task = nil
        sendChain = nil
        registered = false
    }

    private func connectionLost(_ why: String) {
        teardown(closeCode: .abnormalClosure)
        status = .offline
        append(.error, text: why)
        scheduleReconnect()
    }

    private func scheduleReconnect() {
        guard wantsConnection else { return }
        reconnectTask?.cancel()
        let delay = Self.backoffDelay(failures: failures)
        failures += 1
        append(.system, text: String(format: "reconnecting in %.0f s", delay))
        reconnectTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
            guard !Task.isCancelled, let self, self.wantsConnection else { return }
            self.connect(resetBackoff: false)
        }
    }

    /// 1, 2, 4, 8, 16, 32, 60, 60 … seconds.
    nonisolated static func backoffDelay(failures: Int) -> Double {
        min(IRCConfig.maxBackoffSeconds, pow(2, Double(min(failures, 16))))
    }

    // MARK: Sending

    /// Send what the user typed to the channel, and echo it locally (IRC does not echo).
    func sendMessage(_ typed: String) {
        let text = IRCOutgoing.sanitize(typed)
        guard !text.isEmpty else { return }
        guard registered else {
            append(.error, text: "not connected — message not sent")
            return
        }
        sendRaw("PRIVMSG \(IRCConfig.channel) :\(text)")
        append(.own, sender: nickname, text: text)
    }

    private func sendRaw(_ line: String) {
        guard let t = task else { return }
        // Protocol lines are built here from sanitised parts; strip CR/LF once more as a guard.
        let safe = String(String.UnicodeScalarView(line.unicodeScalars.filter { $0 != "\r" && $0 != "\n" }))
        let gen = generation
        // Chain sends so NICK, USER, JOIN … leave in the order they were issued.
        let previous = sendChain
        sendChain = Task { [weak self] in
            await previous?.value
            do {
                try await t.send(.string(safe + "\r\n"))
            } catch {
                guard let self, self.generation == gen else { return }
                self.connectionLost("send failed: \(error.localizedDescription)")
            }
        }
    }

    // MARK: Receiving

    private func handleFrame(_ frame: String) {
        for raw in IRCLine.splitFrame(frame) {
            guard let line = IRCLine.parse(raw) else { continue }
            handle(line)
        }
    }

    private func handle(_ line: IRCLine) {
        switch line.command {
        case "PING":
            sendRaw("PONG :\(line.params.last ?? "")")
        case "001":
            // Welcome: registration is done. Only now is the link "connected", and only now JOIN.
            if let assigned = line.params.first, !assigned.isEmpty { nickname = assigned }
            registered = true
            failures = 0
            status = .connected
            append(.system, text: "connected as \(nickname)")
            sendRaw("JOIN \(IRCConfig.channel)")
        case "433", "432", "436":
            // Nick in use / erroneous / collision: try another number (only matters before 001).
            if !registered {
                let old = nickname
                nickname = IRCConfig.randomNick()
                append(.system, text: "nick \(old) unavailable, trying \(nickname)")
                sendRaw("NICK \(nickname)")
            }
        case "JOIN":
            if line.nick?.caseInsensitiveCompare(nickname) == .orderedSame {
                append(.system, text: "joined \(line.params.first ?? IRCConfig.channel) — type !llm <question>")
            }
        case "NICK":
            if line.nick?.caseInsensitiveCompare(nickname) == .orderedSame, let new = line.params.first {
                nickname = new
            }
        case "PRIVMSG":
            guard line.params.count >= 2, let sender = line.nick else { return }
            let target = line.params[0]
            var text = line.params[line.params.count - 1]
            if text.hasPrefix("\u{1}ACTION "), text.hasSuffix("\u{1}") {
                text = "* \(sender) " + text.dropFirst(8).dropLast()
            } else if text.hasPrefix("\u{1}") {
                return // other CTCP: ignore
            }
            let isChannel = target.caseInsensitiveCompare(IRCConfig.channel) == .orderedSame
            let dim = thinking.isThinking(sender: sender, text: text)
            append(.peer, sender: isChannel ? sender : "\(sender) → you", text: text, thinking: dim)
        case "NOTICE":
            guard registered, let text = line.params.last else { return }
            append(.system, sender: line.nick, text: text)
        case "ERROR":
            connectionLost("server: \(line.params.last ?? "ERROR")")
        case "471", "473", "474", "475", "477":
            append(.error, text: line.params.last ?? "cannot join \(IRCConfig.channel)")
        default:
            break
        }
    }

    private func append(_ kind: ChatMessage.Kind, sender: String? = nil, text: String, thinking: Bool = false) {
        messages.append(ChatMessage(kind: kind, sender: sender, text: text, thinking: thinking))
        if messages.count > IRCConfig.maxHistory {
            messages.removeFirst(messages.count - IRCConfig.maxHistory)
        }
    }
}
