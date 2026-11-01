// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// On-device chat tab: streaming answer, Stop, reasoning in a dimmed "thinking" disclosure.
// With no local model and the PC-bot fallback on (IRC tab), answers come from the PC bot instead.

import SwiftUI

struct ChatView: View {
    @ObservedObject var chat: ChatStore
    @ObservedObject var model: ModelStore
    @State private var input = ""
    @State private var confirmReset = false
    @FocusState private var focused: Bool

    var body: some View {
        VStack(spacing: 0) {
            header
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 10) {
                        ForEach(chat.turns) { turn in row(turn).id(turn.id) }
                        Color.clear.frame(height: 1).id("bottom")
                    }
                    .padding(.horizontal, Theme.historyPadH)
                    .padding(.vertical, Theme.historyPadV)
                }
                .background(Theme.historyBackground)
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: chat.turns.last?.text) { _ in proxy.scrollTo("bottom", anchor: .bottom) }
                .onChange(of: chat.turns.count) { _ in proxy.scrollTo("bottom", anchor: .bottom) }
            }
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            inputRow
        }
        .background(Theme.panelBackground)
        .confirmationDialog("Start a new conversation?", isPresented: $confirmReset, titleVisibility: .visible) {
            Button("Archive history and reset", role: .destructive) { chat.reset() }
        } message: {
            Text("The saved history is moved aside (not deleted), like /llm reset on the PC bot.")
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 2) {
            headerRow
            // Active engine: MLX Swift (primary) or llama.cpp b11960 GGUF (fallback), and why.
            Text("Engine: \(model.engineChoice.active.label) — \(model.engineChoice.reason)")
                .font(.caption2).foregroundColor(Theme.accent.opacity(0.75))
                .lineLimit(2).minimumScaleFactor(0.7)
                .accessibilityIdentifier("activeEngineLabel")
        }
        .padding(.vertical, Theme.titlePadV)
        .padding(.horizontal, Theme.titlePadH)
    }

    private var headerRow: some View {
        HStack(spacing: 6) {
            Circle().fill(model.isLoaded ? Theme.dotConnected : Theme.dotOffline).frame(width: 8, height: 8)
            Text(model.willUseBridge || model.answeringViaBridge
                 ? "CHAT · VIA PC BOT · \(BridgeRequest.botNick.uppercased())"
                 : "CHAT · ON-DEVICE · \(model.engineChoice.active.shortLabel) · \(ModelPin.label.uppercased())")
                .font(Theme.titleFont).tracking(Theme.titleTracking)
                .foregroundColor(Theme.accent).lineLimit(1).minimumScaleFactor(0.6)
            Spacer(minLength: 4)
            Menu("ENGINE") {
                ForEach(EnginePreference.allCases, id: \.self) { p in
                    Button((model.enginePreference == p ? "✓ " : "") + p.label) { model.enginePreference = p }
                }
            }
            .font(Theme.titleFont).foregroundColor(Theme.remote)
            .disabled(chat.generating)
            .accessibilityIdentifier("enginePreferenceMenu")
            Button("RESET") { confirmReset = true }
                .font(Theme.titleFont).foregroundColor(Theme.remote)
                .disabled(chat.generating)
        }
    }

    @ViewBuilder
    private func row(_ turn: ChatTurn) -> some View {
        switch turn.role {
        case .user:
            (Text("you: ").foregroundColor(Theme.ownNick) + Text(turn.text).foregroundColor(Theme.text))
                .font(Theme.font).lineSpacing(Theme.lineSpacing)
                .fixedSize(horizontal: false, vertical: true)
                .textSelection(.enabled)
        case .note:
            Text(turn.text).font(Theme.font).foregroundColor(Theme.system)
                .fixedSize(horizontal: false, vertical: true)
        case .assistant:
            VStack(alignment: .leading, spacing: 4) {
                Text("\(ModelPin.label):").font(Theme.font).foregroundColor(Theme.peerNick)
                let thinking = turn.thinking
                if !thinking.isEmpty || turn.isThinkingNow {
                    DisclosureGroup(turn.isThinkingNow ? "thinking…" : "thinking") {
                        Text(thinking).font(Theme.font).foregroundColor(Theme.text)
                            .fixedSize(horizontal: false, vertical: true)
                            .textSelection(.enabled)
                    }
                    .font(Theme.font)
                    .tint(Theme.system)
                    .opacity(Theme.dimmedOpacity)
                }
                let answer = turn.answer
                if !answer.isEmpty {
                    MarkdownText(text: answer)
                } else if turn.streaming && !turn.isThinkingNow {
                    Text("…").font(Theme.font).foregroundColor(Theme.system)
                }
                if turn.stopped {
                    Text("(stopped)").font(Theme.font).foregroundColor(Theme.system)
                }
                if !turn.streaming, turn.id == chat.turns.last(where: { $0.role == .assistant })?.id,
                   let speed = model.lastSpeed {
                    Text(speed).font(Theme.titleFont).foregroundColor(Theme.system)
                }
            }
        }
    }

    private var inputRow: some View {
        HStack(spacing: Theme.formGap) {
            Text(Theme.prompt).font(Theme.font).foregroundColor(Theme.accent).accessibilityHidden(true)
            TextField("", text: $input, prompt: Text("Ask the on-device model…").foregroundColor(Theme.system),
                      axis: .vertical)
                .lineLimit(1...5)
                .font(Theme.font)
                .foregroundColor(Theme.text)
                .focused($focused)
                .padding(.vertical, Theme.inputPadV)
                .padding(.horizontal, Theme.inputPadH)
                .background(Theme.inputBackground)
                .overlay(RoundedRectangle(cornerRadius: Theme.inputRadius)
                    .stroke(focused ? Theme.accent : Theme.border, lineWidth: Theme.borderWidth))
            if chat.generating {
                Button { chat.stop() } label: {
                    Image(systemName: "stop.fill").foregroundColor(Theme.remote)
                }
                .accessibilityLabel("Stop")
            } else {
                Button(action: send) {
                    Image(systemName: "paperplane.fill").foregroundColor(Theme.accent)
                }
                .disabled(!model.canAnswer || input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .accessibilityLabel("Send")
            }
        }
        .padding(.vertical, Theme.formPadV)
        .padding(.horizontal, Theme.formPadH)
    }

    private func send() {
        chat.send(input)
        input = ""
    }
}
