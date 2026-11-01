// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Clarke Pocket: a small PocketPal-style app — a GGUF model running on the iPhone (llama.cpp,
// Metal) plus an IRC client. Three tabs: Model, Chat, IRC. Works standalone; with no local model
// the chat can optionally fall back to the PC bot over IRC (BridgeFallback.swift). Everything stops cleanly in the
// background (IRC says QUIT, the model is unloaded); nothing calls exit().

import SwiftUI

@main
struct ClarkePocketApp: App {
    @StateObject private var app = AppModel()

    var body: some Scene {
        WindowGroup {
            RootView(app: app)
        }
    }
}

@MainActor
final class AppModel: ObservableObject {
    let model: ModelStore
    let chat: ChatStore
    let irc: IRCClient
    let responder: IRCResponder
    let bridge: BridgeFallback

    init() {
        let m = ModelStore()
        let c = IRCClient()
        model = m
        chat = ChatStore(model: m)
        irc = c
        responder = IRCResponder(model: m, client: c)
        bridge = BridgeFallback(client: c)
        m.attachBridge(bridge, client: c)
    }
}

struct RootView: View {
    @ObservedObject var app: AppModel
    @AppStorage("selectedTab") private var tab = 0
    @Environment(\.scenePhase) private var scenePhase

    /// On unless the `ircAutoConnect` default is set to NO. CI passes `-ircAutoConnect NO` as a
    /// launch argument so the Simulator smoke test never dials the public IRC server; the RECONNECT
    /// button still works. Users never see a change: the key is unset on a phone.
    static var ircAutoConnect: Bool {
        UserDefaults.standard.object(forKey: "ircAutoConnect") == nil
            || UserDefaults.standard.bool(forKey: "ircAutoConnect")
    }

    var body: some View {
        TabView(selection: $tab) {
            ModelView(model: app.model)
                .tabItem { Label("Model", systemImage: "cpu") }.tag(0)
            ChatView(chat: app.chat, model: app.model)
                .tabItem { Label("Chat", systemImage: "bubble.left.and.text.bubble.right") }.tag(1)
            IRCView(client: app.irc, responder: app.responder, model: app.model, bridge: app.bridge)
                .tabItem { Label("IRC", systemImage: "number") }.tag(2)
        }
        .tint(Theme.accent)
        .preferredColorScheme(.dark)
        .onAppear { if Self.ircAutoConnect { app.irc.start() } }
        .onChange(of: scenePhase) { phase in
            switch phase {
            case .active:
                if Self.ircAutoConnect { app.irc.start() }   // reconnect on return (unless the user typed /quit)
            case .background:
                app.irc.stop()             // iOS would suspend the socket anyway
                app.model.enteredBackground()
            default:
                break
            }
        }
    }
}
