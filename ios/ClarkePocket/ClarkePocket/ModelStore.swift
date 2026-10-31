// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Owns the model file and the one LlamaEngine the Chat and IRC tabs share.
//   * Download: URLSession download task with progress, then a streaming CryptoKit SHA-256 check
//     against ModelPin, then rename from .partial. Resumable after Cancel / a dropped connection.
//   * Import: Files picker → copy into the app → GGUF magic → SHA-256. A file whose hash is not
//     the pinned one is kept but labelled "custom (unverified)".
//   * Storage: Application Support/Models, excluded from iCloud/iTunes backup (1.1 GB).
//   * Load/unload: Metal, ctx 2048, threads from the P-cores; low-memory warning before loading;
//     unloaded when the app goes to the background or iOS sends a memory warning.
//   * One generation at a time (`busy`); the IRC responder skips while the chat is generating.
//   * Fallback: when there is no local model (no file, or it failed to load) and the user switched
//     on the PC-bot fallback, `generate` asks the bridge's IRC bot instead (BridgeFallback.swift).
//     A low-memory refusal is not a fallback case: the user decides "Load anyway".
// Nothing here exits the app; every failure becomes a visible state.

import Foundation
import SwiftUI
import UIKit
import Combine

@MainActor
final class ModelStore: NSObject, ObservableObject {
    enum FileState: Equatable {
        case missing
        case downloading(received: Int64, total: Int64)
        case copying
        case verifying(done: Int64, total: Int64)
        case ready(verified: Bool)
        case failed(String)
    }
    enum EngineState: Equatable {
        case unloaded
        case loading
        case loaded(String)   // human description
        case failed(String)
    }

    @Published private(set) var file: FileState = .missing
    @Published private(set) var engineState: EngineState = .unloaded
    @Published private(set) var busy = false
    /// Set when loading was refused for memory; the view offers "Load anyway".
    @Published private(set) var memoryWarning: String?
    @Published private(set) var lastSpeed: String?

    let engine = LlamaEngine()
    /// Optional PC-bot fallback (set once by AppModel).
    private(set) var bridge: BridgeFallback?
    private var bridgeWatch: [AnyCancellable] = []
    /// True while the current answer comes from the PC bot rather than this phone.
    @Published private(set) var answeringViaBridge = false

    private var session: URLSession!
    private var download: URLSessionDownloadTask?
    private var resumeData: Data?
    private var verifyTask: Task<Void, Never>?
    private let cancelVerify = Flag()
    private var memoryObserver: NSObjectProtocol?

    nonisolated static let modelsDir: URL = {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let dir = base.appendingPathComponent("Models", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        var d = dir
        excludeFromBackup(&d)
        return dir
    }()
    nonisolated static var pinnedURL: URL { modelsDir.appendingPathComponent(ModelPin.fileName) }
    nonisolated static var customURL: URL { modelsDir.appendingPathComponent("custom.gguf") }
    nonisolated static var partialURL: URL { modelsDir.appendingPathComponent(ModelPin.fileName + ".partial") }

    nonisolated static func excludeFromBackup(_ url: inout URL) {
        var v = URLResourceValues()
        v.isExcludedFromBackup = true
        try? url.setResourceValues(v)
    }

    /// The file the engine loads: the pinned model if present, else an imported custom one.
    var activeFile: URL? {
        if FileManager.default.fileExists(atPath: Self.pinnedURL.path) { return Self.pinnedURL }
        if FileManager.default.fileExists(atPath: Self.customURL.path) { return Self.customURL }
        return nil
    }
    var isLoaded: Bool { if case .loaded = engineState { return true } else { return false } }

    /// Chat can send: a local model file exists, or the PC-bot fallback is on and IRC is connected.
    var canAnswer: Bool { activeFile != nil || (bridge?.isAvailable ?? false) }
    /// No local model file, so the next answer would come from the PC bot.
    var willUseBridge: Bool { activeFile == nil && (bridge?.isAvailable ?? false) }

    /// Wire the fallback; views watching this store also refresh when it or IRC changes state.
    func attachBridge(_ b: BridgeFallback, client: IRCClient) {
        bridge = b
        bridgeWatch = [
            b.objectWillChange.sink { [weak self] _ in self?.objectWillChange.send() },
            client.objectWillChange.sink { [weak self] _ in self?.objectWillChange.send() },
        ]
    }

    override init() {
        super.init()
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 60
        cfg.waitsForConnectivity = true
        session = URLSession(configuration: cfg, delegate: self, delegateQueue: nil)
        refreshFileState()
        memoryObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor in self?.handleMemoryWarning() }
        }
    }

    /// Files already on disk: trust a pinned file that has the exact pinned size (it was hashed
    /// before the rename); the user can re-check with "Verify again".
    func refreshFileState() {
        if let size = FileVerifier.fileSize(Self.pinnedURL), size == ModelPin.sizeBytes {
            file = .ready(verified: true)
        } else if FileManager.default.fileExists(atPath: Self.customURL.path) {
            file = .ready(verified: false)
        } else if case .downloading = file {
            // keep
        } else {
            file = .missing
        }
    }

    // MARK: Download

    func startDownload() {
        guard download == nil else { return }
        memoryWarning = nil
        let task: URLSessionDownloadTask
        if let data = resumeData {
            task = session.downloadTask(withResumeData: data)
            resumeData = nil
        } else {
            task = session.downloadTask(with: ModelPin.url)
        }
        download = task
        file = .downloading(received: 0, total: ModelPin.sizeBytes)
        task.resume()
    }

    func cancelDownload() {
        guard let task = download else { return }
        task.cancel { [weak self] data in
            Task { @MainActor in
                self?.resumeData = data
                self?.download = nil
                self?.file = .missing
            }
        }
    }

    var canResume: Bool { resumeData != nil }

    fileprivate func downloadProgress(received: Int64, total: Int64) {
        guard download != nil else { return }
        file = .downloading(received: received, total: total > 0 ? total : ModelPin.sizeBytes)
    }

    fileprivate func downloadFinished(partial: URL?, error: String?) {
        download = nil
        guard let partial, error == nil else {
            file = .failed(error ?? "download failed")
            return
        }
        verify(partial, pinnedOnly: true)
    }

    fileprivate func downloadFailed(_ message: String, resume: Data?) {
        download = nil
        if let resume { resumeData = resume }
        file = .failed(message + (resume != nil ? " — tap Download to resume" : ""))
    }

    // MARK: Verify / import

    /// Hash `src` off the main thread. Pinned hash → the pinned file name; otherwise, for imports,
    /// keep it as custom.gguf (unverified); for downloads, delete it and report the mismatch.
    private func verify(_ src: URL, pinnedOnly: Bool) {
        cancelVerify.set(false)
        let cancel = cancelVerify
        let total = FileVerifier.fileSize(src) ?? 0
        file = .verifying(done: 0, total: total)
        verifyTask = Task.detached(priority: .userInitiated) { [weak self] in
            var lastReport = Date.distantPast
            let result: Result<String, Error> = Result {
                guard FileVerifier.hasGGUFMagic(src) else { throw VerifyError.notGGUF }
                return try FileVerifier.sha256Hex(of: src, progress: { done in
                    let now = Date()
                    guard now.timeIntervalSince(lastReport) > 0.2 else { return }
                    lastReport = now
                    Task { @MainActor in self?.file = .verifying(done: done, total: total) }
                }, shouldContinue: { !cancel.get() })
            }
            await self?.finishVerify(result, src: src, size: total, pinnedOnly: pinnedOnly)
        }
    }

    private func finishVerify(_ result: Result<String, Error>, src: URL, size: Int64, pinnedOnly: Bool) {
        verifyTask = nil
        let fm = FileManager.default
        switch result {
        case .failure(let e):
            try? fm.removeItem(at: src)
            file = .failed("check failed: \(e)")
        case .success(let hex):
            let matches = hex == ModelPin.sha256 && size == ModelPin.sizeBytes
            if !matches && pinnedOnly {
                try? fm.removeItem(at: src)
                file = .failed("download corrupted: \(VerifyError.wrongHash(expected: ModelPin.sha256, actual: hex)) — deleted, try again")
                return
            }
            let target = matches ? Self.pinnedURL : Self.customURL
            try? fm.removeItem(at: target)
            do {
                try fm.moveItem(at: src, to: target)
                var t = target
                Self.excludeFromBackup(&t)
                file = .ready(verified: matches)
            } catch {
                file = .failed("could not store the model: \(error.localizedDescription)")
            }
        }
    }

    func cancelVerification() { cancelVerify.set(true) }

    /// "Verify again" for a file already in place.
    func reverify() {
        guard let url = activeFile else { return }
        unload()
        let tmp = url.appendingPathExtension("partial")
        try? FileManager.default.removeItem(at: tmp)
        do { try FileManager.default.moveItem(at: url, to: tmp) } catch {
            file = .failed("could not re-check: \(error.localizedDescription)")
            return
        }
        verify(tmp, pinnedOnly: false)
    }

    /// From `.fileImporter`: copy (1 GB) off the main thread, then verify.
    func importFile(_ picked: URL) {
        unload()
        file = .copying
        let dest = Self.modelsDir.appendingPathComponent("import.gguf.partial")
        Task.detached(priority: .userInitiated) { [weak self] in
            let ok = picked.startAccessingSecurityScopedResource()
            defer { if ok { picked.stopAccessingSecurityScopedResource() } }
            do {
                try? FileManager.default.removeItem(at: dest)
                try FileManager.default.copyItem(at: picked, to: dest)
                await self?.verifyImported(dest)
            } catch {
                await self?.setFailed("import failed: \(error.localizedDescription)")
            }
        }
    }

    private func verifyImported(_ url: URL) { verify(url, pinnedOnly: false) }
    private func setFailed(_ s: String) { file = .failed(s) }

    func deleteModel() {
        unload()
        for u in [Self.pinnedURL, Self.customURL, Self.partialURL] { try? FileManager.default.removeItem(at: u) }
        resumeData = nil
        file = .missing
    }

    // MARK: Engine

    /// Load the model. Refuses (once) when iOS reports too little free memory; `force` overrides.
    func load(force: Bool = false) async {
        guard let url = activeFile else { engineState = .failed("no model file — download or import one"); return }
        if isLoaded || engineState == .loading { return }
        let modelBytes = FileVerifier.fileSize(url) ?? ModelPin.sizeBytes
        if !force, case let .low(need, avail) = RuntimePolicy.memoryAdvice(
            available: MemoryMonitor.availableBytes(), modelBytes: modelBytes) {
            memoryWarning = "iOS reports \(RuntimePolicy.formatBytes(avail)) free for this app; the model needs about \(RuntimePolicy.formatBytes(need)). Close other apps, or load anyway (iOS may close Clarke Pocket)."
            return
        }
        memoryWarning = nil
        engineState = .loading
        do {
            let info = try await engine.load(path: url.path, threads: MemoryMonitor.threads())
            engineState = .loaded("\(info.description) · ctx \(info.contextTokens) · \(info.threads.gen)/\(info.threads.batch) threads · Metal · template \(info.templateSource) · T \(info.temperature) p \(info.topP)")
        } catch {
            engineState = .failed("\(error)")
        }
    }

    func unload() {
        cancelCurrent()
        engineState = .unloaded
        Task { await engine.unload() }
    }

    private func handleMemoryWarning() {
        guard isLoaded else { return }
        unload()
        engineState = .failed("unloaded after an iOS memory warning — tap Load to try again")
    }

    /// App moved to the background: Metal work is not allowed there, and the memory is better
    /// given back. The chat reloads the model on the next message.
    func enteredBackground() {
        if isLoaded { unload() }
    }

    // MARK: Generation (one at a time)

    private var current: Task<(String, Bool, String?), Never>?

    /// Stream one answer. `onText` gets each new piece of text on the main actor.
    /// Returns the full raw text (with <think>…</think>), or nil if busy / not loaded / failed.
    func generate(system: String, history: [PromptTurn], user: String, maxTokens: Int,
                  onText: @escaping @MainActor (String) -> Void) async -> (text: String, stopped: Bool, error: String?)? {
        guard !busy else { return nil }
        busy = true
        defer { busy = false }
        if !isLoaded, activeFile != nil { await load() }
        if !isLoaded {
            // Local model unavailable (no file, or loading failed). Not after a low-memory refusal.
            guard memoryWarning == nil, let bridge, bridge.isAvailable else { return nil }
            return await generateViaBridge(bridge, user: user, onText: onText)
        }
        let engine = self.engine
        let task = Task { @MainActor () -> (String, Bool, String?) in
            var out = ""
            var stopped = false
            var failure: String?
            do {
                let turns = await engine.fitPrompt(system: system, history: history, user: user)
                let start = Date()
                var count = 0
                _ = try await engine.begin(turns, maxTokens: maxTokens)
                while let piece = try await engine.next() {
                    if Task.isCancelled { await engine.cancel(); stopped = true; break }
                    count += 1
                    if !piece.isEmpty { out += piece; onText(piece) }
                }
                if Task.isCancelled { stopped = true }
                let secs = Date().timeIntervalSince(start)
                if secs > 0 { self.lastSpeed = String(format: "%d tokens · %.1f tok/s", count, Double(count) / secs) }
            } catch {
                failure = "\(error)"
            }
            return (out, stopped, failure)
        }
        current = task
        let r = await task.value
        current = nil
        return (r.0, r.1, r.2)
    }



    /// The PC bot keeps its own per-nick history and system prompt, so only `user` is sent.
    private func generateViaBridge(_ bridge: BridgeFallback, user: String,
                                   onText: @escaping @MainActor (String) -> Void) async -> (text: String, stopped: Bool, error: String?) {
        answeringViaBridge = true
        defer { answeringViaBridge = false }
        let task = Task { @MainActor () -> (String, Bool, String?) in
            let r = await bridge.ask(question: user, onText: onText)
            return (r.text, r.stopped, r.error)
        }
        current = task
        let r = await task.value
        current = nil
        lastSpeed = "via PC bot \(BridgeRequest.botNick) (IRC private message)"
        return (r.0, r.1, r.2)
    }

    func cancelCurrent() { current?.cancel() }
}

extension ModelStore: URLSessionDownloadDelegate {
    nonisolated func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                                didWriteData bytesWritten: Int64, totalBytesWritten: Int64,
                                totalBytesExpectedToWrite: Int64) {
        Task { @MainActor in self.downloadProgress(received: totalBytesWritten, total: totalBytesExpectedToWrite) }
    }

    nonisolated func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                                didFinishDownloadingTo location: URL) {
        // The temp file is deleted when this returns: move it now, synchronously.
        let partial = ModelStore.partialURL
        let status = (downloadTask.response as? HTTPURLResponse)?.statusCode ?? 0
        guard status == 200 else {
            Task { @MainActor in self.downloadFinished(partial: nil, error: "server answered HTTP \(status)") }
            return
        }
        do {
            try? FileManager.default.removeItem(at: partial)
            try FileManager.default.moveItem(at: location, to: partial)
            Task { @MainActor in self.downloadFinished(partial: partial, error: nil) }
        } catch {
            let msg = error.localizedDescription
            Task { @MainActor in self.downloadFinished(partial: nil, error: "could not save: \(msg)") }
        }
    }

    nonisolated func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        guard let error else { return }
        let ns = error as NSError
        if ns.code == NSURLErrorCancelled { return }   // cancelDownload() already handled it
        let resume = ns.userInfo[NSURLSessionDownloadTaskResumeData] as? Data
        let msg = error.localizedDescription
        Task { @MainActor in self.downloadFailed(msg, resume: resume) }
    }
}

/// A thread-safe Bool (the hashing thread polls it for Cancel).
final class Flag: @unchecked Sendable {
    private let lock = NSLock()
    private var value = false
    func set(_ v: Bool) { lock.lock(); value = v; lock.unlock() }
    func get() -> Bool { lock.lock(); defer { lock.unlock() }; return value }
}
