// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The TeaVM rhythm page's left chat column (GitHub Pages: axiomiccoreness.github.io/hello_world.py),
// mapped value-for-value. Source of every value:
//   games/teavm-rhythm/src/main/webapp/index.html  (main @ a4c94f1eddbf1736dfb1c73f9e004a27082654c4)
// CSS rem = 16 pt here (the page sets no root font-size, so the browser default 16 px applies).
// No colour below is invented: the page has no nick palette, status-dot colour or "thinking"
// style of its own, so those reuse existing page values (noted per line).

import SwiftUI

extension Color {
    /// `#rrggbb` (or `rrggbb`) → sRGB colour. Invalid input gives clear, so a typo is visible.
    init(hex: String) {
        let h = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        guard h.count == 6, let v = UInt32(h, radix: 16) else {
            self = .clear
            return
        }
        self.init(.sRGB,
                  red: Double((v >> 16) & 0xff) / 255,
                  green: Double((v >> 8) & 0xff) / 255,
                  blue: Double(v & 0xff) / 255,
                  opacity: 1)
    }
}

enum Theme {
    // MARK: Colours
    /// `#cli-column { background: #0e141c }` — index.html:87; also `#cli-form { background: #0e141c }` — :107
    static let panelBackground = Color(hex: "#0e141c")
    /// `#chat-history { background: #0a1018 }` — index.html:102
    static let historyBackground = Color(hex: "#0a1018")
    /// `#chat-input { background: #0a1018 }` — index.html:112
    static let inputBackground = Color(hex: "#0a1018")
    /// `#cli-column { color: #d7e0ea }` — :87; `#chat-history { color }` — :101; `#chat-input { color }` — :112
    static let text = Color(hex: "#d7e0ea")
    /// `border: 1px solid #243041` — #cli-column :86, .cli-title border-bottom :93,
    /// #cli-form border-top :107, #chat-input :113
    static let border = Color(hex: "#243041")
    /// `.cli-title { color: #5eead4 }` — :94; `.ps1 { color: #5eead4 }` — :109;
    /// `#chat-input:focus { border-color: #5eead4 }` — :116
    static let accent = Color(hex: "#5eead4")
    /// `.cli-title .remote { color: #fbbf24 }` — index.html:97 (the host label in the title bar)
    static let remote = Color(hex: "#fbbf24")
    /// `body.theme-ar .note { color: #8890a8 }` — index.html:79 (muted text on the dark theme)
    static let note = Color(hex: "#8890a8")

    // Reused page values for things the page itself does not colour (no new colours):
    /// Own nick: the prompt colour `.ps1` (#5eead4, :109) — what the user types is teal on the page.
    static let ownNick = accent
    /// Other nicks (the !llm bot included): the title's `.remote` host colour (#fbbf24, :97).
    static let peerNick = remote
    /// System / status lines: `.note` (#8890a8, :79).
    static let system = note
    /// Status dot: connected = accent (:94), connecting = remote (:97), offline = note (:79).
    static let dotConnected = accent
    static let dotConnecting = remote
    static let dotOffline = note

    // MARK: Opacity
    /// Dimmed `[thinking]` lines: the page's only dimming rule,
    /// `#autoplay-btn.locked, .picker.locked { opacity: 0.55 }` — index.html:54 and :61.
    static let dimmedOpacity = 0.55

    // MARK: Type
    /// `#cli-column { font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, … }` — index.html:88.
    /// `ui-monospace` on iOS *is* SF Mono, i.e. `.monospaced` design.
    static let fontSize: CGFloat = 12
    static let lineHeight: CGFloat = 1.4
    /// SwiftUI lineSpacing is the extra gap between lines: 12 × (1.4 − 1) = 4.8.
    static let lineSpacing: CGFloat = fontSize * (lineHeight - 1)
    static let font = Font.system(size: fontSize, design: .monospaced)
    /// `.cli-title { font-size: 0.72rem }` = 11.52 — index.html:94
    static let titleFont = Font.system(size: 0.72 * 16, design: .monospaced)
    /// `.cli-title { letter-spacing: 0.04em }` (em of 11.52) — :94; `text-transform: uppercase` — :95
    static let titleTracking: CGFloat = 0.04 * 0.72 * 16
    /// `<span class="ps1">›</span>` — index.html:127
    static let prompt = "›"

    // MARK: Shape
    /// `#cli-column { border-radius: 6px }` — index.html:86 (0 under 900 px wide, :69; we keep 0 on iPhone)
    static let panelRadius: CGFloat = 6
    /// `#chat-input { border-radius: 4px }` — index.html:113
    static let inputRadius: CGFloat = 4
    /// All borders are 1px — :86, :93, :107, :113
    static let borderWidth: CGFloat = 1

    // MARK: Spacing (rem × 16)
    /// `.cli-title { padding: 0.45rem 0.65rem }` — index.html:93
    static let titlePadV: CGFloat = 0.45 * 16, titlePadH: CGFloat = 0.65 * 16
    /// `#chat-history { padding: 0.55rem 0.65rem }` — index.html:100
    static let historyPadV: CGFloat = 0.55 * 16, historyPadH: CGFloat = 0.65 * 16
    /// `#cli-form { padding: 0.4rem 0.55rem; gap: 0.35rem }` — index.html:105-106
    static let formPadV: CGFloat = 0.4 * 16, formPadH: CGFloat = 0.55 * 16, formGap: CGFloat = 0.35 * 16
    /// `#chat-input { padding: 0.35rem 0.45rem }` — index.html:114
    static let inputPadV: CGFloat = 0.35 * 16, inputPadH: CGFloat = 0.45 * 16
}
