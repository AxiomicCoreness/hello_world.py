// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import PocketCore

final class IRCCommandTests: XCTestCase {
    let ch = "#axiomiccoreness"

    func lines(_ s: String) -> [String] {
        if case .send(let l, _) = IRCCommand.build(s, channel: ch) { return l }
        return []
    }
    func isError(_ s: String) -> Bool {
        if case .error = IRCCommand.build(s, channel: ch) { return true }
        return false
    }

    func testPlainTextAndDoubleSlash() {
        XCTAssertEqual(lines("hello"), ["PRIVMSG #axiomiccoreness :hello"])
        XCTAssertEqual(lines("//join is literal"), ["PRIVMSG #axiomiccoreness :/join is literal"])
        XCTAssertTrue(isError("   "))
        if case .send(_, let echo) = IRCCommand.build("hi", channel: ch) {
            XCTAssertEqual(echo, .init(target: ch, text: "hi", isAction: false))
        } else { XCTFail() }
    }

    func testInjectionIsFlattened() {
        // A pasted CR/LF can never start a second protocol line.
        XCTAssertEqual(lines("hi\r\nQUIT :pwned"), ["PRIVMSG #axiomiccoreness :hi  QUIT :pwned"])
        XCTAssertEqual(lines("/msg bob hi\nPRIVMSG x :y"), ["PRIVMSG bob :hi PRIVMSG x :y"])
        XCTAssertEqual(lines("/join #a\r\nJOIN #b").count, 0)  // becomes "/join #a  JOIN #b" → error
        XCTAssertTrue(isError("/join #a\r\nJOIN #b"))
        // Typed CTCP is stripped.
        XCTAssertEqual(lines("\u{1}VERSION\u{1}"), ["PRIVMSG #axiomiccoreness :VERSION"])
        for l in lines("x\u{0}y") { XCTAssertFalse(l.contains("\u{0}")) }
    }

    func testJoinPartNickQuit() {
        XCTAssertEqual(lines("/join #test"), ["JOIN #test"])
        XCTAssertEqual(lines("/JOIN #test"), ["JOIN #test"])
        XCTAssertTrue(isError("/join test"))
        XCTAssertTrue(isError("/join #a,#b"))
        XCTAssertTrue(isError("/join #a key"))
        XCTAssertEqual(lines("/part"), ["PART #axiomiccoreness"])
        XCTAssertEqual(lines("/part #x bye now"), ["PART #x :bye now"])
        XCTAssertEqual(lines("/part going home"), ["PART #axiomiccoreness :going home"])
        XCTAssertEqual(lines("/nick Clarke_2"), ["NICK Clarke_2"])
        XCTAssertTrue(isError("/nick 9lives"))
        XCTAssertTrue(isError("/nick a b"))
        XCTAssertTrue(isError("/nick " + String(repeating: "a", count: 31)))
        XCTAssertEqual(IRCCommand.build("/quit", channel: ch), .quit(line: "QUIT :Clarke Pocket"))
        XCTAssertEqual(IRCCommand.build("/quit later", channel: ch), .quit(line: "QUIT :later"))
        XCTAssertTrue(isError("/kick bob"))
        XCTAssertTrue(isError("/raw PRIVMSG x :y"))
    }

    func testMsgAndMe() {
        XCTAssertEqual(lines("/msg NickServ help"), ["PRIVMSG NickServ :help"])
        XCTAssertEqual(lines("/msg #other hi there"), ["PRIVMSG #other :hi there"])
        XCTAssertTrue(isError("/msg bob"))
        XCTAssertTrue(isError("/msg :bad hi"))
        XCTAssertEqual(lines("/me waves"), ["PRIVMSG #axiomiccoreness :\u{1}ACTION waves\u{1}"])
        XCTAssertTrue(isError("/me"))
        let long = lines("/me " + String(repeating: "é", count: 400))[0]
        let text = long.components(separatedBy: " :")[1]
        XCTAssertLessThanOrEqual(text.utf8.count, IRCOutgoing.maxTextBytes)
        XCTAssertTrue(text.hasSuffix("\u{1}"))
    }

    func testValidators() {
        XCTAssertTrue(IRCCommand.isValidChannel("#a"))
        XCTAssertTrue(IRCCommand.isValidChannel("&local"))
        XCTAssertFalse(IRCCommand.isValidChannel("#"))
        XCTAssertFalse(IRCCommand.isValidChannel("#a:b"))
        XCTAssertFalse(IRCCommand.isValidChannel("#a\u{7}"))
        XCTAssertTrue(IRCCommand.isValidNick("[Clarke]_^"))
        XCTAssertFalse(IRCCommand.isValidNick("-x"))
        XCTAssertFalse(IRCCommand.isValidNick(""))
        XCTAssertFalse(IRCCommand.isValidNick("é"))
    }
}
