// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// UI smoke test: launch the real app in the Simulator, visit Model / Chat / IRC, and attach a
// screenshot of each. No typing, no chat line sent, no model loaded. `-ircAutoConnect NO` keeps
// the app off the public IRC server; `-ircResponderEnabled NO` keeps the !llm answerer off.

import XCTest

final class LaunchSmokeUITests: XCTestCase {
    override func setUp() { continueAfterFailure = false }

    private func shot(_ app: XCUIApplication, _ name: String) {
        let a = XCTAttachment(screenshot: app.screenshot())
        a.name = name
        a.lifetime = .keepAlways
        add(a)
    }

    func testLaunchAndVisitEveryTab() {
        let app = XCUIApplication()
        app.launchArguments = ["-ircAutoConnect", "NO", "-ircResponderEnabled", "NO", "-selectedTab", "0"]
        app.launch()
        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 30))

        let tabs = app.tabBars.firstMatch
        XCTAssertTrue(tabs.waitForExistence(timeout: 30), "tab bar never appeared")
        for name in ["Model", "Chat", "IRC"] {
            XCTAssertTrue(tabs.buttons[name].exists, "missing tab \(name)")
        }

        // No model file in a fresh Simulator: the Model tab offers the download.
        let notDownloaded = app.staticTexts.containing(NSPredicate(format: "label CONTAINS %@", "Not downloaded")).firstMatch
        XCTAssertTrue(notDownloaded.waitForExistence(timeout: 15), "Model tab did not show the download state")
        shot(app, "1-model-tab")

        tabs.buttons["Chat"].tap()
        XCTAssertTrue(tabs.buttons["Chat"].isSelected)
        shot(app, "2-chat-tab")

        tabs.buttons["IRC"].tap()
        XCTAssertTrue(tabs.buttons["IRC"].isSelected)
        shot(app, "3-irc-tab")

        XCTAssertEqual(app.state, .runningForeground, "app did not stay up")
    }
}
