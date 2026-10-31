// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Copied (not moved) from ios/AxiomicCorenessChat/AxiomicCorenessChat/IRCClient.swift at
// db2b966bc03d153803ee174415843b2134c35a1e (PR #165), then adapted for Clarke Pocket:
//   * typed input goes through IRCCommand (/join /part /msg /me /nick /quit, //text),
//   * an active channel that follows /join and /part instead of one fixed channel,
//   * /quit closes the socket and stays offline until "Reconnect" (the app never exits),
//   * an `onChannelMessage` hook the on-device !llm responder listens to, and `say(lines:)`,
//   * an `onDirectMessage` hook (PMs and NOTICEs to us) and `sendPrivate(_:to:)` for the
//     chat's PC-bot fallback (BridgeFallback.swift).
//
// Direct IRC client over WebSocket (abjects network by default). The phone talks to abjects
// itself; nothing on the user's PC is exposed (no open port, no tunnel, no all-interfaces bind).
//
// Lifecycle: connect only while the app is in the foreground (RootView drives this from
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
    /// abjects' browser WebSocket gateway — the URL its own webchat (https://www.abjects.net/chat.html)
    /// dials, and the Pages chatbox default. Probed from GitHub runners: HTTP 101 + 001 welcome.
    static let gatewayURL = URL(string: "wss://irc.abjects.net:6680/")!
    /// Shown in the title bar and status text.
    static let networkName = "abjects"
    static let gatewayLabel = "irc.abjects.net"
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
final class IRCClient: ObservableObject {
    enum Status: Equatable { case offline, connecting, connected }

    @Published private(set) var messages: [ChatMessage] = []
    @Published private(set) var status: Status = .offline
    @Published private(set) var nickname = IRCConfig.randomNick()
    /// Where plain text goes. Follows our own JOIN / PART; starts at IRCConfig.channel.
    @Published private(set) var activeChannel = IRCConfig.channel

    /// Called for every channel PRIVMSG from someone else: (sender, channel, text).
    var onChannelMessage: ((String, String, String) -> Void)?
    /// (sender, text, isNotice) for a PRIVMSG addressed to our nick or a NOTICE from a user.
    var onDirectMessage: ((String, String, Bool) -> Void)?

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
        sendRaw("USER \(nickname) 0 * :Clarke Pocket iOS")

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

    /// Send what the user typed: plain text to the active channel, or a slash command.
    /// Local echo for messages (IRC does not echo your own lines).
    func sendInput(_ typed: String) {
        switch IRCCommand.build(typed, channel: activeChannel) {
        case .error(let note):
            append(.error, text: note)
        case .send(let lines, let echo):
            guard registered else {
                append(.error, text: "not connected — not sent")
                return
            }
            lines.forEach(sendRaw)
            if let e = echo {
                let toActive = e.target.caseInsensitiveCompare(activeChannel) == .orderedSame
                let who = toActive ? nickname : "\(nickname) → \(e.target)"
                append(.own, sender: who, text: e.isAction ? "* \(nickname) \(e.text)" : e.text)
            }
        case .quit(let line):
            if registered { sendRaw(line) }
            wantsConnection = false
            reconnectTask?.cancel()
            reconnectTask = nil
            append(.system, text: "disconnected (/quit) — tap Reconnect to come back")
            // Give the QUIT a moment to leave before closing; the app itself stays open.
            let gen = generation
            Task { [weak self] in
                try? await Task.sleep(nanoseconds: 500_000_000)
                guard let self, self.generation == gen else { return }
                self.teardown(closeCode: .normalClosure)
                self.status = .offline
            }
        }
    }

    /// Lines from the on-device responder: sent as-is to `channel` (already sanitised, ≤ 400 bytes)
    /// and echoed locally.
    func say(lines: [String], to channel: String) {
        guard registered else { return }
        for l in lines {
            let text = IRCOutgoing.sanitize(l)
            guard !text.isEmpty else { continue }
            sendRaw("PRIVMSG \(channel) :\(text)")
            append(.own, sender: nickname, text: text)
        }
    }

    /// One private message (the chat's PC-bot fallback), sanitised and echoed locally.
    func sendPrivate(_ text: String, to nick: String) {
        guard registered else { return }
        let clean = IRCOutgoing.sanitize(text)
        guard !clean.isEmpty, !nick.isEmpty, !nick.contains(" ") else { return }
        sendRaw("PRIVMSG \(nick) :\(clean)")
        append(.own, sender: "\(nickname) → \(nick)", text: clean)
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
            sendRaw("JOIN \(activeChannel)")
        case "433", "432", "436":
            // Nick in use / erroneous / collision: try another number (only matters before 001).
            if !registered {
                let old = nickname
                nickname = IRCConfig.randomNick()
                append(.system, text: "nick \(old) unavailable, trying \(nickname)")
                sendRaw("NICK \(nickname)")
            }
        case "JOIN":
            if line.nick?.caseInsensitiveCompare(nickname) == .orderedSame, let chan = line.params.first {
                activeChannel = chan
                append(.system, text: "joined \(chan) — plain text goes here · \(IRCCommand.help)")
            }
        case "PART":
            if line.nick?.caseInsensitiveCompare(nickname) == .orderedSame, let chan = line.params.first {
                append(.system, text: "left \(chan)")
                if chan.caseInsensitiveCompare(activeChannel) == .orderedSame {
                    append(.system, text: "no active channel — /join #channel")
                }
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
            let isChannel = target.hasPrefix("#") || target.hasPrefix("&")
            let dim = thinking.isThinking(sender: sender, text: text)
            let label = isChannel
                ? (target.caseInsensitiveCompare(activeChannel) == .orderedSame ? sender : "\(sender) @ \(target)")
                : "\(sender) → you"
            append(.peer, sender: label, text: text, thinking: dim)
            if isChannel, !line.params[line.params.count - 1].hasPrefix("\u{1}") {
                onChannelMessage?(sender, target, line.params[line.params.count - 1])
            } else if !isChannel, target.caseInsensitiveCompare(nickname) == .orderedSame {
                onDirectMessage?(sender, line.params[line.params.count - 1], false)
            }
        case "NOTICE":
            guard registered, let text = line.params.last else { return }
            append(.system, sender: line.nick, text: text)
            if let from = line.nick { onDirectMessage?(from, text, true) }
        case "ERROR":
            connectionLost("server: \(line.params.last ?? "ERROR")")
        case "471", "473", "474", "475", "477":
            append(.error, text: line.params.last ?? "cannot join that channel")
        default:
            break
        }
    }

    /// A local note in the IRC log (used by the responder for status lines).
    func note(_ text: String, error: Bool = false) { append(error ? .error : .system, text: text) }

    private func append(_ kind: ChatMessage.Kind, sender: String? = nil, text: String, thinking: Bool = false) {
        messages.append(ChatMessage(kind: kind, sender: sender, text: text, thinking: thinking))
        if messages.count > IRCConfig.maxHistory {
            messages.removeFirst(messages.count - IRCConfig.maxHistory)
        }
    }
}
