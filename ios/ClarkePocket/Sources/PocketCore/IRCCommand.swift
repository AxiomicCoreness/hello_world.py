// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// What the IRC shell's input line may send. Plain text is a PRIVMSG to the active channel.
// A leading "/" selects one of a fixed set of commands — /join /part /msg /me /nick /quit — and
// each one is BUILT here from validated parts. Nothing typed is ever passed through raw, so
// "/quote", "/raw", "/oper", "/kill", CR/LF smuggling or a second command on the line all fail.
// "//text" sends the literal text "/text".

import Foundation

public enum IRCInput: Equatable, Sendable {
    /// Protocol lines to send, in order (no CR/LF inside; the client appends "\r\n").
    case send(lines: [String], echo: Echo?)
    /// Close the connection after sending these lines (no exit(): the app stays open).
    case quit(line: String)
    /// Nothing to send; show this note.
    case error(String)

    /// What to show locally for an outgoing message (IRC does not echo your own lines).
    public struct Echo: Equatable, Sendable {
        public var target: String
        public var text: String
        public var isAction: Bool
    }
}

public enum IRCCommand {
    public static let allowed = ["/join", "/part", "/msg", "/me", "/nick", "/quit"]
    public static var help: String { "commands: " + allowed.joined(separator: " ") + "  (//text sends /text)" }

    /// RFC 2812 channel: starts with # & + or !, 2…50 chars, no space, comma, BEL, NUL, CR, LF or ':'.
    public static func isValidChannel(_ s: String) -> Bool {
        guard let f = s.first, "#&+!".contains(f), (2...50).contains(s.count) else { return false }
        return !s.unicodeScalars.contains { $0 == " " || $0 == "," || $0 == "\u{7}" || $0 == "\u{0}"
            || $0 == "\r" || $0 == "\n" || $0 == ":" }
    }

    /// RFC 2812 nick (length relaxed to 30, as most networks allow):
    /// first char letter or one of []\`_^{|}, then letters, digits, those specials or '-'.
    public static func isValidNick(_ s: String) -> Bool {
        guard (1...30).contains(s.unicodeScalars.count) else { return false }
        let special = "[]\\`_^{|}"
        for (i, u) in s.unicodeScalars.enumerated() {
            let isLetter = ("a"..."z").contains(u) || ("A"..."Z").contains(u)
            let isDigit = ("0"..."9").contains(u)
            let isSpecial = special.unicodeScalars.contains(u)
            if i == 0 { guard isLetter || isSpecial else { return false } }
            else { guard isLetter || isDigit || isSpecial || u == "-" else { return false } }
        }
        return true
    }

    /// Message text for PRIVMSG/PART/QUIT trailing params: CR/LF/NUL removed, CTCP \u{1} removed
    /// (so a typed message can't forge a CTCP), 400-byte cap.
    public static func cleanText(_ s: String, maxBytes: Int = IRCOutgoing.maxTextBytes) -> String {
        IRCOutgoing.sanitize(String(String.UnicodeScalarView(s.unicodeScalars.filter { $0 != "\u{1}" })),
                             maxBytes: maxBytes)
    }

    /// Split off the first whitespace-delimited word.
    static func firstWord(_ s: Substring) -> (String, Substring) {
        let t = s.drop(while: { $0 == " " || $0 == "\t" })
        guard let sp = t.firstIndex(where: { $0 == " " || $0 == "\t" }) else { return (String(t), "") }
        return (String(t[..<sp]), t[sp...].drop(while: { $0 == " " || $0 == "\t" }))
    }

    /// Turn one typed line into protocol lines. `channel` is the active channel.
    public static func build(_ typed: String, channel: String) -> IRCInput {
        // Any CR/LF in the input line is treated as a space before parsing: one line, one command.
        let input = String(String.UnicodeScalarView(typed.unicodeScalars.map {
            ($0 == "\r" || $0 == "\n") ? " " : $0 })).trimmingCharacters(in: .whitespaces)
        guard !input.isEmpty else { return .error("nothing to send") }

        if input.hasPrefix("//") || !input.hasPrefix("/") {
            let text = cleanText(input.hasPrefix("//") ? String(input.dropFirst()) : input)
            guard !text.isEmpty else { return .error("nothing to send") }
            return .send(lines: ["PRIVMSG \(channel) :\(text)"],
                         echo: .init(target: channel, text: text, isAction: false))
        }

        let (cmdRaw, rest) = firstWord(Substring(input))
        let cmd = cmdRaw.lowercased()
        switch cmd {
        case "/join":
            let (chan, more) = firstWord(rest)
            guard isValidChannel(chan) else { return .error("usage: /join #channel") }
            guard more.isEmpty else { return .error("usage: /join #channel (one channel, no key)") }
            return .send(lines: ["JOIN \(chan)"], echo: nil)

        case "/part":
            var (chan, reasonRaw) = firstWord(rest)
            if chan.isEmpty { chan = channel }
            else if !isValidChannel(chan) { reasonRaw = rest; chan = channel }
            let reason = cleanText(String(reasonRaw))
            return .send(lines: [reason.isEmpty ? "PART \(chan)" : "PART \(chan) :\(reason)"], echo: nil)

        case "/msg":
            let (target, textRaw) = firstWord(rest)
            guard isValidNick(target) || isValidChannel(target) else { return .error("usage: /msg <nick|#channel> <text>") }
            let text = cleanText(String(textRaw))
            guard !text.isEmpty else { return .error("usage: /msg <nick|#channel> <text>") }
            return .send(lines: ["PRIVMSG \(target) :\(text)"],
                         echo: .init(target: target, text: text, isAction: false))

        case "/me":
            // 400 bytes minus "\u{1}ACTION " and the closing "\u{1}".
            let text = cleanText(String(rest), maxBytes: IRCOutgoing.maxTextBytes - 9)
            guard !text.isEmpty else { return .error("usage: /me <action>") }
            return .send(lines: ["PRIVMSG \(channel) :\u{1}ACTION \(text)\u{1}"],
                         echo: .init(target: channel, text: text, isAction: true))

        case "/nick":
            let (nick, more) = firstWord(rest)
            guard isValidNick(nick), more.isEmpty else { return .error("usage: /nick <newnick> (letters, digits, []\\`_^{|}-, max 30)") }
            return .send(lines: ["NICK \(nick)"], echo: nil)

        case "/quit":
            let reason = cleanText(String(rest))
            return .quit(line: "QUIT :\(reason.isEmpty ? "Clarke Pocket" : reason)")

        default:
            return .error("unknown command \(cmdRaw) — \(help)")
        }
    }
}
