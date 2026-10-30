// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import PocketCore

final class SegmenterTests: XCTestCase {
    func testProseMathCode() {
        let text = MarkdownMath.normalizeMath("So \\(x^2\\) is **big**:\n\\[\\sum_i i\\]\nthen\n```swift\nlet a = \"\\\\(no)\"\n```\nend")
        let blocks = ReplySegmenter.segment(text)
        XCTAssertEqual(blocks, [
            .prose([.markdown("So "), .math("x^2"), .markdown(" is **big**:")]),
            .displayMath("\\sum_i i"),
            .prose([.markdown("then")]),
            .code(language: "swift", body: "let a = \"\\\\(no)\""),
            .prose([.markdown("end")]),
        ])
    }

    func testMathInsideCodeSpanStaysCode() {
        XCTAssertEqual(ReplySegmenter.segment("use `\\(x\\)` literally"),
                       [.prose([.markdown("use `\\(x\\)` literally")])])
    }

    func testEmpty() {
        XCTAssertEqual(ReplySegmenter.segment(""), [])
    }
}
