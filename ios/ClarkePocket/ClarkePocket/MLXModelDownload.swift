// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Downloads Clarke Yoursa Tee's own MLX 4-bit model (MLXModelPin.selected) from this repo's
// GitHub release into Application Support/Models/MLX/<dir>, checking every file's size and
// SHA-256 against the pin before it is kept. Nothing else is downloaded.

import Foundation

@MainActor
final class MLXModelDownload: ObservableObject {
    enum State: Equatable {
        case idle
        case downloading(file: String, index: Int, count: Int)
        case verified
        case failed(String)
    }
    @Published private(set) var state: State = .idle
    private var task: Task<Void, Never>?

    func refresh() {
        guard let pin = MLXModelPin.selected, let dir = EngineDetector.mlxModelDirectory() else { state = .idle; return }
        if case .verified = MLXModelState.check(dir: dir, pin: pin) { state = .verified }
        else if case .downloading = state {} else { state = .idle }
    }

    func start(onDone: @escaping @MainActor () -> Void) {
        guard task == nil, let pin = MLXModelPin.selected, var dir = EngineDetector.mlxModelDirectory() else { return }
        task = Task { [weak self] in
            do {
                try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
                ModelStore.excludeFromBackup(&dir)
                for (i, f) in pin.files.enumerated() {
                    let dest = dir.appendingPathComponent(f.name)
                    if FileVerifier.fileSize(dest) == f.sizeBytes, (try? FileVerifier.sha256Hex(of: dest)) == f.sha256 { continue }
                    self?.state = .downloading(file: f.name, index: i + 1, count: pin.files.count)
                    let (tmp, resp) = try await URLSession.shared.download(from: pin.url(for: f))
                    guard (resp as? HTTPURLResponse)?.statusCode == 200 else { throw MLXEngineError.unavailable("HTTP error for \(f.name)") }
                    guard FileVerifier.fileSize(tmp) == f.sizeBytes, try FileVerifier.sha256Hex(of: tmp) == f.sha256 else {
                        try? FileManager.default.removeItem(at: tmp)
                        throw MLXEngineError.unavailable("\(f.name) does not match its pinned size/SHA-256")
                    }
                    try? FileManager.default.removeItem(at: dest)
                    try FileManager.default.moveItem(at: tmp, to: dest)
                }
                self?.state = .verified
                onDone()
            } catch is CancellationError {
                self?.state = .idle
            } catch {
                self?.state = .failed("\(error)")
            }
            self?.task = nil
        }
    }

    func cancel() { task?.cancel(); task = nil; state = .idle }
}
