// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Renders a saved/streamed reply: Markdown inline styles (bold, italics, `code`, links) via
// AttributedString, LaTeX math shown as its source in the accent colour (monospace), display
// math and code blocks on their own scrollable lines. No web view, no JS, nothing fetched.

import SwiftUI

struct MarkdownText: View {
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            ForEach(Array(ReplySegmenter.segment(text).enumerated()), id: \.offset) { _, block in
                switch block {
                case .prose(let runs):
                    runs.reduce(Text("")) { acc, run in acc + Self.text(for: run) }
                        .font(Theme.font)
                        .foregroundColor(Theme.text)
                        .lineSpacing(Theme.lineSpacing)
                        .fixedSize(horizontal: false, vertical: true)
                case .displayMath(let tex):
                    ScrollView(.horizontal, showsIndicators: false) {
                        Text(tex).font(Theme.font).foregroundColor(Theme.accent).padding(.vertical, 2)
                    }
                    .frame(maxWidth: .infinity, alignment: .center)
                case .code(let lang, let body):
                    VStack(alignment: .leading, spacing: 2) {
                        if !lang.isEmpty { Text(lang).font(Theme.titleFont).foregroundColor(Theme.system) }
                        ScrollView(.horizontal, showsIndicators: false) {
                            Text(body).font(Theme.font).foregroundColor(Theme.text)
                        }
                    }
                    .padding(6)
                    .background(Theme.panelBackground)
                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(Theme.border, lineWidth: Theme.borderWidth))
                }
            }
        }
        .textSelection(.enabled)
    }

    static func text(for run: InlineRun) -> Text {
        switch run {
        case .math(let tex):
            return Text(tex).foregroundColor(Theme.accent)
        case .markdown(let s):
            let opts = AttributedString.MarkdownParsingOptions(interpretedSyntax: .inlineOnlyPreservingWhitespace,
                                                               failurePolicy: .returnPartiallyParsedIfPossible)
            if let a = try? AttributedString(markdown: s, options: opts) { return Text(a) }
            return Text(s)
        }
    }
}
