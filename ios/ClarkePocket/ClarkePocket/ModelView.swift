// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Model tab: download (with progress and SHA-256 check), import from Files, load/unload, memory.

import SwiftUI
import UniformTypeIdentifiers

struct ModelView: View {
    @ObservedObject var model: ModelStore
    @State private var importing = false
    @State private var confirmDelete = false
    @State private var available: Int64 = MemoryMonitor.availableBytes()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                section("MODEL") {
                    line("name", ModelPin.label)
                    line("file", ModelPin.fileName)
                    line("size", "\(RuntimePolicy.formatBytes(ModelPin.sizeBytes)) (\(ModelPin.sizeBytes) bytes)")
                    line("sha256", ModelPin.sha256)
                    line("source", "GitHub release \(ModelPin.releaseTag)")
                }
                section("FILE") { fileState }
                section("ENGINE") { engineState }
                section("MEMORY") {
                    line("free for this app", available > 0 ? RuntimePolicy.formatBytes(available) : "unknown")
                    line("needs about", RuntimePolicy.formatBytes(RuntimePolicy.estimatedNeed(modelBytes: ModelPin.sizeBytes)))
                    Text("The weights are memory-mapped from the file, so iOS can page them; the KV cache for 2048 tokens is about 57 MB. Unloaded automatically when the app goes to the background or iOS warns about memory.")
                        .foregroundColor(Theme.system)
                    Button("Refresh") { available = MemoryMonitor.availableBytes() }
                        .foregroundColor(Theme.accent)
                }
            }
            .font(Theme.font)
            .foregroundColor(Theme.text)
            .padding(12)
        }
        .background(Theme.historyBackground)
        .fileImporter(isPresented: $importing, allowedContentTypes: [.data, .item]) { result in
            if case .success(let url) = result { model.importFile(url) }
        }
        .confirmationDialog("Delete the model file?", isPresented: $confirmDelete, titleVisibility: .visible) {
            Button("Delete", role: .destructive) { model.deleteModel() }
        }
        .onAppear { model.refreshFileState(); available = MemoryMonitor.availableBytes() }
    }

    @ViewBuilder private var fileState: some View {
        switch model.file {
        case .missing:
            Text("Not downloaded. Download over Wi-Fi (1.12 GB) and keep the app open until it finishes, or import a .gguf from Files.")
                .foregroundColor(Theme.system)
            HStack {
                button(model.canResume ? "Resume download" : "Download") { model.startDownload() }
                button("Import from Files") { importing = true }
            }
        case let .downloading(received, total):
            ProgressView(value: Double(received), total: Double(max(total, 1))).tint(Theme.accent)
            line("downloaded", "\(RuntimePolicy.formatBytes(received)) of \(RuntimePolicy.formatBytes(total))")
            button("Cancel (can resume)") { model.cancelDownload() }
        case .copying:
            ProgressView().tint(Theme.accent)
            Text("Copying the file into the app…").foregroundColor(Theme.system)
        case let .verifying(done, total):
            ProgressView(value: Double(done), total: Double(max(total, 1))).tint(Theme.accent)
            line("checking SHA-256", "\(RuntimePolicy.formatBytes(done)) of \(RuntimePolicy.formatBytes(total))")
            button("Cancel check") { model.cancelVerification() }
        case .ready(let verified):
            line("status", verified ? "ready · SHA-256 matches the pinned model" : "custom / unverified (hash differs from the pinned model)")
            HStack {
                button("Verify again") { model.reverify() }
                button("Import other") { importing = true }
                Button("Delete") { confirmDelete = true }.foregroundColor(Theme.remote)
            }
        case .failed(let why):
            Text(why).foregroundColor(Theme.remote)
            HStack {
                button(model.canResume ? "Resume download" : "Download again") { model.startDownload() }
                button("Import from Files") { importing = true }
            }
        }
    }

    @ViewBuilder private var engineState: some View {
        switch model.engineState {
        case .unloaded:
            Text("Not loaded. The Chat tab loads it on the first message.").foregroundColor(Theme.system)
            button("Load now") { Task { await model.load() } }.disabled(model.activeFile == nil)
        case .loading:
            ProgressView().tint(Theme.accent)
            Text("Loading onto the GPU (Metal)…").foregroundColor(Theme.system)
        case .loaded(let desc):
            Text(desc)
            button("Unload (free memory)") { model.unload() }.disabled(model.busy)
        case .failed(let why):
            Text(why).foregroundColor(Theme.remote)
            button("Try again") { Task { await model.load() } }.disabled(model.activeFile == nil)
        }
        if let warn = model.memoryWarning {
            Text(warn).foregroundColor(Theme.remote)
            button("Load anyway") { Task { await model.load(force: true) } }
        }
    }

    private func section<C: View>(_ title: String, @ViewBuilder _ content: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(Theme.titleFont).tracking(Theme.titleTracking).foregroundColor(Theme.accent)
            content()
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.panelBackground)
        .overlay(RoundedRectangle(cornerRadius: Theme.panelRadius).stroke(Theme.border, lineWidth: Theme.borderWidth))
    }

    private func line(_ k: String, _ v: String) -> some View {
        (Text(k + ": ").foregroundColor(Theme.system) + Text(v).foregroundColor(Theme.text))
            .fixedSize(horizontal: false, vertical: true)
            .textSelection(.enabled)
    }

    private func button(_ title: String, _ action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .buttonStyle(.bordered)
            .tint(Theme.accent)
    }
}
