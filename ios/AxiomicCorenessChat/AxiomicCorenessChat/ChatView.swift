// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The page's left CLI column (title bar · history · "›" input row), rebuilt in SwiftUI with the
// values in Theme.swift. Connects only while the app is in the foreground.

import SwiftUI

struct ChatView: View {
    @StateObject private var client = LiberaIRCClient()
    @State private var inputText = ""
    @FocusState private var inputFocused: Bool
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        VStack(spacing: 0) {
            titleBar
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            history
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            inputRow
        }
        .background(Theme.panelBackground)
        .overlay(
            RoundedRectangle(cornerRadius: Theme.panelRadius)
                .stroke(Theme.border, lineWidth: Theme.borderWidth)
        )
        .clipShape(RoundedRectangle(cornerRadius: Theme.panelRadius))
        .padding(.horizontal, 4)
        .background(Theme.historyBackground.ignoresSafeArea())
        .preferredColorScheme(.dark)
        .onAppear { client.start() }
        .onDisappear { client.stop() }
        .onChange(of: scenePhase) { phase in
            switch phase {
            case .active: client.start()          // reconnect on return to the foreground
            case .background: client.stop()       // iOS would suspend the socket anyway
            default: break
            }
        }
    }

    // `.cli-title`: teal, uppercase, letter-spaced; host label in `.remote` amber.
    private var titleBar: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(dotColor)
                .frame(width: 8, height: 8)
                .accessibilityLabel(statusText)
            (Text("CLI · ").foregroundColor(Theme.accent)
             + Text("web.libera.chat").foregroundColor(Theme.remote)
             + Text(" → \(IRCConfig.channel.uppercased()) · !LLM").foregroundColor(Theme.accent))
                .font(Theme.titleFont)
                .tracking(Theme.titleTracking)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Spacer(minLength: 4)
            Button("RECONNECT") { client.reconnectNow() }
                .font(Theme.titleFont)
                .tracking(Theme.titleTracking)
                .foregroundColor(Theme.accent)
        }
        .padding(.vertical, Theme.titlePadV)
        .padding(.horizontal, Theme.titlePadH)
        .background(Theme.panelBackground)
    }

    // `#chat-history`: monospace 12/1.4 on #0a1018, wrapped, newest at the bottom.
    private var history: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: Theme.lineSpacing) {
                    ForEach(client.messages) { msg in
                        row(msg).id(msg.id)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, Theme.historyPadV)
                .padding(.horizontal, Theme.historyPadH)
            }
            .background(Theme.historyBackground)
            .scrollDismissesKeyboard(.interactively)
            .onChange(of: client.messages.last?.id) { last in
                guard let last else { return }
                withAnimation(.easeOut(duration: 0.15)) { proxy.scrollTo(last, anchor: .bottom) }
            }
        }
        .contentShape(Rectangle())
        .onTapGesture { inputFocused = true }   // page: `#cli-column { cursor: text }`, click focuses input
    }

    @ViewBuilder
    private func row(_ msg: ChatMessage) -> some View {
        Group {
            switch msg.kind {
            case .own, .peer:
                (Text(msg.sender ?? "?")
                    .foregroundColor(msg.kind == .own ? Theme.ownNick : Theme.peerNick)
                 + Text(": ").foregroundColor(Theme.system)
                 + Text(msg.text).foregroundColor(Theme.text))
            case .system:
                Text((msg.sender.map { "-\($0)- " } ?? "") + msg.text).foregroundColor(Theme.system)
            case .error:
                Text("! " + msg.text).foregroundColor(Theme.remote)
            }
        }
        .font(Theme.font)
        .lineSpacing(Theme.lineSpacing)
        .fixedSize(horizontal: false, vertical: true)
        .textSelection(.enabled)
        .opacity(msg.thinking ? Theme.dimmedOpacity : 1)
    }

    // `#cli-form`: "›" prompt + bordered input; Enter sends (page: "Enter to send").
    private var inputRow: some View {
        HStack(spacing: Theme.formGap) {
            Text(Theme.prompt)
                .font(Theme.font)
                .foregroundColor(Theme.accent)
                .accessibilityHidden(true)
            TextField("", text: $inputText,
                      prompt: Text("Type !llm ...").foregroundColor(Theme.system))
                .font(Theme.font)
                .foregroundColor(Theme.text)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
                .submitLabel(.send)
                .focused($inputFocused)
                .onSubmit(send)
                .padding(.vertical, Theme.inputPadV)
                .padding(.horizontal, Theme.inputPadH)
                .background(Theme.inputBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: Theme.inputRadius)
                        .stroke(inputFocused ? Theme.accent : Theme.border, lineWidth: Theme.borderWidth)
                )
            Button(action: send) {
                Image(systemName: "paperplane.fill").foregroundColor(Theme.accent)
            }
            .disabled(!client.isConnected)
            .accessibilityLabel("Send")
        }
        .padding(.vertical, Theme.formPadV)
        .padding(.horizontal, Theme.formPadH)
        .background(Theme.panelBackground)
    }

    private func send() {
        guard !inputText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        client.sendMessage(inputText)
        inputText = ""
        inputFocused = true
    }

    private var dotColor: Color {
        switch client.status {
        case .connected: return Theme.dotConnected
        case .connecting: return Theme.dotConnecting
        case .offline: return Theme.dotOffline
        }
    }

    private var statusText: String {
        switch client.status {
        case .connected: return "Connected to Libera as \(client.nickname)"
        case .connecting: return "Connecting"
        case .offline: return "Disconnected"
        }
    }
}
