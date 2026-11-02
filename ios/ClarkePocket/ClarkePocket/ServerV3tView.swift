// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// "Server (v3t)" engine screen: owner token in the iOS Keychain (entered here, never bundled),
// shared server-side history list, chat through the authenticated bridge route.
// Does not change the default engine, the iOS default pin, or MODEL_PIN.json.

import Security
import SwiftUI
import PocketCore

enum OwnerTokenKeychain {
    static let service = "io.github.axiomiccoreness.clarkepocket.v3t"
    static let account = "owner"

    static func read() -> String? {
        let q: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                kSecAttrService as String: service, kSecAttrAccount as String: account,
                                kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var out: AnyObject?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess, let d = out as? Data else { return nil }
        return String(data: d, encoding: .utf8)
    }

    @discardableResult static func save(_ token: String) -> Bool {
        delete()
        let q: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                kSecAttrService as String: service, kSecAttrAccount as String: account,
                                kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                                kSecValueData as String: Data(token.utf8)]
        return SecItemAdd(q as CFDictionary, nil) == errSecSuccess
    }

    static func delete() {
        SecItemDelete([kSecClass as String: kSecClassGenericPassword,
                       kSecAttrService as String: service, kSecAttrAccount as String: account] as CFDictionary)
    }
}

struct ServerV3tSettingsView: View {
    @AppStorage("serverV3tBase") private var base = ServerV3tClient.defaultBase
    @State private var tokenField = ""
    @State private var hasToken = OwnerTokenKeychain.read() != nil

    var body: some View {
        Form {
            Section("Server (v3t) bridge") {
                TextField("Bridge URL", text: $base).textInputAutocapitalization(.never).autocorrectionDisabled()
            }
            Section(hasToken ? "Owner token: saved in Keychain" : "Owner token") {
                SecureField("Paste owner token", text: $tokenField)
                Button("Save to Keychain") {
                    hasToken = OwnerTokenKeychain.save(tokenField.trimmingCharacters(in: .whitespacesAndNewlines))
                    tokenField = ""
                }.disabled(tokenField.isEmpty)
                if hasToken { Button("Forget token", role: .destructive) { OwnerTokenKeychain.delete(); hasToken = false } }
            }
        }.navigationTitle("Server (v3t)")
    }
}

struct ServerV3tChatView: View {
    @AppStorage("serverV3tBase") private var base = ServerV3tClient.defaultBase
    @State private var conversations: [ServerV3tConversation] = []
    @State private var current: String?
    @State private var lines: [ServerV3tMessage] = []
    @State private var draft = ""
    @State private var status = ""
    @State private var busy = false

    private func client() throws -> ServerV3tClient {
        try ServerV3tClient(base: base, token: OwnerTokenKeychain.read() ?? "")
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Menu(current ?? "New chat") {
                    Button("New chat") { current = nil; lines = [] }
                    ForEach(conversations, id: \.conversation_id) { c in
                        Button(c.title.isEmpty ? c.conversation_id : c.title) { Task { await open(c.conversation_id) } }
                    }
                }
                Spacer()
                Button("Sync") { Task { await sync() } }
                NavigationLink("Settings") { ServerV3tSettingsView() }
            }.padding(8)
            List(Array(lines.enumerated()), id: \.offset) { _, m in
                VStack(alignment: .leading) {
                    Text(m.role == "user" ? "Clarke Yoursa Tee" : "v3t").font(.caption).foregroundStyle(.secondary)
                    Text(m.content).textSelection(.enabled)
                }
            }
            if !status.isEmpty { Text(status).font(.caption).foregroundStyle(.secondary) }
            HStack {
                TextField("Message v3t", text: $draft, axis: .vertical)
                Button("Send") { Task { await send() } }.disabled(draft.isEmpty || busy)
            }.padding(8)
        }
        .navigationTitle("Server (v3t)")
        .task { await sync() }
    }

    func sync() async {
        do { conversations = try await client().conversations(); status = "\(conversations.count) shared conversation(s)" }
        catch { status = describe(error) }
    }

    func open(_ id: String) async {
        do { lines = try await client().messages(id); current = id } catch { status = describe(error) }
    }

    func send() async {
        let text = draft; draft = ""; busy = true; defer { busy = false }
        lines.append(ServerV3tMessage(role: "user", content: text, ts: "", device: "iphone", model_sha256: nil))
        do {
            let (reply, conv) = try await client().send(text, conversationID: current)
            current = conv
            lines.append(ServerV3tMessage(role: "assistant", content: reply, ts: "", device: nil, model_sha256: nil))
            await sync()
        } catch { status = describe(error) }
    }

    func describe(_ e: Error) -> String {
        switch e as? ServerV3tError {
        case .noToken?: return "Add the owner token in Settings"
        case .unauthorized?: return "Token rejected (401) — re-enter or re-mint"
        case .badURL?: return "Bridge URL must be https:// (or http://127.0.0.1)"
        default: return "Server unreachable: \(e.localizedDescription)"
        }
    }
}
