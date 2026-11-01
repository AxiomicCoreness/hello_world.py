// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// The real (non-stub) client for the PC-side Ray/CUDA backend: one GET to
// http://127.0.0.1:<port>/healthz, nothing else. iOS has no CUDA; this only asks the PC.
// Never opens a listening socket. OFF by default (Model tab).

import Foundation

struct LoopbackRayCUDARemote: RayCUDARemote {
    let endpoint: String

    func health() async throws -> RayCUDAHealth {
        let url = try RayCUDARemoteConfig.healthURL(for: endpoint)
        var req = URLRequest(url: url, timeoutInterval: 5)
        req.httpMethod = "GET"
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        return try RayCUDAHealth.decode(data)
    }
}
