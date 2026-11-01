// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Two Model-tab panels:
//   CONNECTOME — the bundled HHMIJaneliaMap.xml, always shown as a placeholder (3-neuron ring,
//                not HHMI Janelia FlyEM data), plus an on-demand run labelled as a simulation.
//   PC BACKENDS — the PC-side Ray/CUDA backend: OFF by default, remote only (iOS has no CUDA),
//                 loopback endpoint only, a health check and nothing else. Chat never uses it.

import SwiftUI

private func panel<C: View>(_ title: String, @ViewBuilder _ content: () -> C) -> some View {
    VStack(alignment: .leading, spacing: 6) {
        Text(title).font(Theme.titleFont).tracking(Theme.titleTracking).foregroundColor(Theme.accent)
        content()
    }
    .padding(10)
    .frame(maxWidth: .infinity, alignment: .leading)
    .background(Theme.panelBackground)
    .overlay(RoundedRectangle(cornerRadius: Theme.panelRadius).stroke(Theme.border, lineWidth: Theme.borderWidth))
}

private func kv(_ k: String, _ v: String) -> some View {
    (Text(k + ": ").foregroundColor(Theme.system) + Text(v).foregroundColor(Theme.text))
        .fixedSize(horizontal: false, vertical: true)
}

enum BundledConnectome {
    /// The bundled placeholder map, or the error text.
    static func load() -> Result<Connectome, String> {
        guard let url = Bundle.main.url(forResource: "HHMIJaneliaMap", withExtension: "xml") else {
            return .failure("\(Connectome.placeholderFileName) is not in the app bundle")
        }
        do { return .success(try Connectome.parse(try Data(contentsOf: url), isPlaceholder: true)) }
        catch { return .failure("\(error)") }
    }
}

struct ConnectomePanel: View {
    @State private var map = BundledConnectome.load()
    @State private var raster: [[String]]?

    var body: some View {
        panel("CONNECTOME (PLACEHOLDER)") {
            kv("file", Connectome.placeholderLabel)
            switch map {
            case .failure(let e):
                Text(e).foregroundColor(Theme.remote)
            case .success(let c):
                kv("neurons", "\(c.neurons.count) (\(c.neurons.joined(separator: ", ")))")
                kv("connections", c.synapses.map { "\($0.from)→\($0.to) \($0.weight)" }.joined(separator: ", "))
                if let r = raster {
                    Text(ConnectomeSimulation.label).foregroundColor(Theme.remote)
                    ForEach(Array(r.enumerated()), id: \.offset) { i, s in
                        kv("step \(i)", s.isEmpty ? "—" : s.joined(separator: " "))
                    }
                } else if let first = c.neurons.first {
                    Button("Run simulation (stimulate \(first))") {
                        raster = ConnectomeSimulation().run(c, stimulate: first, steps: 6)
                    }
                    .buttonStyle(.bordered).tint(Theme.accent)
                }
            }
        }
        .accessibilityIdentifier("connectomePanel")
    }
}

struct RemoteBackendPanel: View {
    @AppStorage(RayCUDARemoteConfig.enabledKey) private var enabled = false
    @AppStorage(RayCUDARemoteConfig.endpointKey) private var endpoint = RayCUDARemoteConfig.defaultEndpoint
    @State private var status: String?
    @State private var checking = false

    var body: some View {
        panel("PC BACKENDS (REMOTE)") {
            kv("this iPhone", ComputeBackend.onDevice.label)
            kv("fallback", ComputeBackend.pcBotIRC.label)
            Toggle(isOn: $enabled) { Text(ComputeBackend.pcRayCUDA.label).foregroundColor(Theme.text) }
                .tint(Theme.accent)
            Text("iOS has no CUDA: CUDA kernels run only on your PC, under Ray. Off by default. The app only asks the PC's health endpoint at 127.0.0.1 (reachable from the Simulator on that PC, or through a forwarded port); Chat does not send anything to it. This repo has no PC-side Ray/CUDA service yet, so expect “not reachable”.")
                .foregroundColor(Theme.system)
            if enabled {
                TextField("http://127.0.0.1:<port>", text: $endpoint)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .foregroundColor(Theme.text)
                Button(checking ? "Checking…" : "Check PC backend") { check() }
                    .disabled(checking)
                    .buttonStyle(.bordered).tint(Theme.accent)
                if let s = status { Text(s).foregroundColor(Theme.remote) }
            }
        }
    }

    private func check() {
        let ep = endpoint
        checking = true
        status = nil
        Task {
            let text: String
            do {
                _ = try RayCUDARemoteConfig.healthURL(for: ep)
                text = (try await LoopbackRayCUDARemote(endpoint: ep).health()).summary
            } catch let e as RemoteEndpointError {
                text = e.description
            } catch {
                text = "not reachable: \(error.localizedDescription)"
            }
            await MainActor.run { status = text; checking = false }
        }
    }
}
