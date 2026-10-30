// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// IRC tab: the page's CLI column (same layout and Theme as PR #165's ChatView), plus slash
// commands, the active channel in the title, and the "answer !llm on this phone" switch.

import SwiftUI

struct IRCView: View {
    @ObservedObject var client: IRCClient
    @ObservedObject var responder: IRCResponder
    @ObservedObject var model: ModelStore
    @State private var inputText = ""
    @FocusState private var inputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            titleBar
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            responderBar
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            history
            Rectangle().fill(Theme.border).frame(height: Theme.borderWidth)
            inputRow
        }
        .background(Theme.panelBackground)
    }

    private var titleBar: some View {
        HStack(spacing: 6) {
            Circle().fill(dotColor).frame(width: 8, height: 8).accessibilityLabel(statusText)
            (Text("IRC · ").foregroundColor(Theme.accent)
             + Text(IRCConfig.gatewayLabel).foregroundColor(Theme.remote)
             + Text(" → \(client.activeChannel.uppercased())").foregroundColor(Theme.accent))
                .font(Theme.titleFont).tracking(Theme.titleTracking)
                .lineLimit(1).minimumScaleFactor(0.7)
            Spacer(minLength: 4)
            Button("RECONNECT") { client.reconnectNow() }
                .font(Theme.titleFont).tracking(Theme.titleTracking).foregroundColor(Theme.accent)
        }
        .padding(.vertical, Theme.titlePadV)
        .padding(.horizontal, Theme.titlePadH)
    }

    private var responderBar: some View {
        Toggle(isOn: $responder.enabled) {
            Text(responder.enabled
                 ? (model.isLoaded ? "answering !llm here with the on-device model" : "!llm on — load the model to answer")
                 : "answer !llm with the on-device model (off)")
                .font(Theme.titleFont).foregroundColor(responder.enabled ? Theme.accent : Theme.system)
        }
        .tint(Theme.accent)
        .padding(.vertical, 4)
        .padding(.horizontal, Theme.titlePadH)
    }

    private var history: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: Theme.lineSpacing) {
                    ForEach(client.messages) { msg in row(msg).id(msg.id) }
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
        .onTapGesture { inputFocused = true }
    }

    @ViewBuilder
    private func row(_ msg: ChatMessage) -> some View {
        Group {
            switch msg.kind {
            case .own, .peer:
                (Text(msg.sender ?? "?").foregroundColor(msg.kind == .own ? Theme.ownNick : Theme.peerNick)
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

    private var inputRow: some View {
        HStack(spacing: Theme.formGap) {
            Text(Theme.prompt).font(Theme.font).foregroundColor(Theme.accent).accessibilityHidden(true)
            TextField("", text: $inputText,
                      prompt: Text("message, !llm …, or /join /msg /me /nick /part /quit").foregroundColor(Theme.system))
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
                .overlay(RoundedRectangle(cornerRadius: Theme.inputRadius)
                    .stroke(inputFocused ? Theme.accent : Theme.border, lineWidth: Theme.borderWidth))
            Button(action: send) { Image(systemName: "paperplane.fill").foregroundColor(Theme.accent) }
                .disabled(!client.isConnected)
                .accessibilityLabel("Send")
        }
        .padding(.vertical, Theme.formPadV)
        .padding(.horizontal, Theme.formPadH)
    }

    private func send() {
        guard !inputText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        client.sendInput(inputText)
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
        case .connected: return "Connected to \(IRCConfig.networkName) as \(client.nickname)"
        case .connecting: return "Connecting"
        case .offline: return "Disconnected"
        }
    }
}
