// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// Small pure decisions the llama.cpp wrapper makes, kept here so they are unit-tested on Linux:
// thread counts, the low-memory warning, which history turns fit the context, and BOS handling.

import Foundation

public enum RuntimePolicy {
    /// Context length for the phone: 2048 tokens (KV cache ≈ 57 MiB in f16 for this 28-layer model).
    public static let contextTokens: Int32 = 2048
    /// Tokens reserved for the answer when packing history into the prompt.
    public static let replyReserve = 768
    /// Max tokens generated for one chat answer (R1-style models think first, so this is generous).
    public static let maxChatTokens = 1024
    /// Max tokens for an IRC !llm answer (kept short: the channel only gets ≤ 4 lines anyway).
    public static let maxIRCTokens = 640
    /// Offload every layer to Metal.
    public static let gpuLayers: Int32 = 99

    /// Threads for generation / prompt batches. With all layers on Metal the CPU mostly feeds the
    /// GPU, so use the performance cores (A14: 2) for generation and P + 2 for batches, never
    /// more than total − 1 so the UI thread stays smooth. Unknown P-core count → total / 3.
    public static func threads(performanceCores: Int?, totalCores: Int) -> (gen: Int32, batch: Int32) {
        let total = max(1, totalCores)
        let p = max(1, min(performanceCores ?? max(1, total / 3), total))
        let gen = min(p, max(1, total - 1))
        let batch = min(p + 2, max(1, total - 1))
        return (Int32(gen), Int32(max(gen, batch)))
    }

    public enum MemoryAdvice: Equatable, Sendable {
        case ok
        /// Loading may get the app killed by iOS (jetsam). Show `needed` vs `available` (bytes).
        case low(needed: Int64, available: Int64)
        /// The OS did not tell us (simulator / Linux).
        case unknown
    }

    /// Bytes the model needs resident beyond what iOS can page back from the mmapped file:
    /// KV cache + Metal compute buffers + slack ≈ 512 MiB, plus 25 % of the weights for
    /// buffers that are copied rather than mapped. Conservative on purpose.
    public static func estimatedNeed(modelBytes: Int64) -> Int64 {
        512 * 1024 * 1024 + modelBytes / 4
    }

    /// `available` is `os_proc_available_memory()` (0 means "not reported").
    public static func memoryAdvice(available: Int64, modelBytes: Int64) -> MemoryAdvice {
        guard available > 0 else { return .unknown }
        let need = estimatedNeed(modelBytes: modelBytes)
        return available < need ? .low(needed: need, available: available) : .ok
    }

    /// Bytes as "1.04 GB" (decimal, like Files.app).
    public static func formatBytes(_ b: Int64) -> String {
        let gb = Double(b) / 1_000_000_000
        if gb >= 1 { return String(format: "%.2f GB", gb) }
        return String(format: "%.0f MB", Double(b) / 1_000_000)
    }

    /// GGUF chat templates that print `bos_token` themselves expect the prompt to start with BOS.
    /// llama.cpp's built-in template renderer never emits it, and this model's GGUF says
    /// add_bos_token = false, so we prepend BOS ourselves in exactly that case.
    public static func shouldPrependBOS(template: String?, vocabAddsBOS: Bool, promptStartsWithBOS: Bool) -> Bool {
        guard !vocabAddsBOS, !promptStartsWithBOS, let t = template else { return false }
        return t.contains("bos_token")
    }
}

/// A turn as fed back to the model (answers only — thinking is never re-sent, as in the bridge).
public struct PromptTurn: Equatable, Sendable {
    public var role: String   // "system" | "user" | "assistant"
    public var content: String
    public init(role: String, content: String) { self.role = role; self.content = content }
}

public enum PromptWindow {
    /// Keep the newest history that fits: walk back over whole user/assistant pairs while
    /// `tokenCount(system + kept + new user)` stays ≤ budget. Always keeps the system prompt and
    /// the new message; drops an orphan leading assistant turn. `tokenCount` is the real
    /// tokenizer on the phone; tests pass a stand-in.
    public static func fit(system: String, history: [PromptTurn], user: String, budget: Int,
                           tokenCount: ([PromptTurn]) -> Int) -> [PromptTurn] {
        let head = [PromptTurn(role: "system", content: system)]
        let tail = [PromptTurn(role: "user", content: user)]
        var kept: [PromptTurn] = []
        var i = history.count
        while i > 0 {
            // Take one turn at a time, then check (so an over-long single answer is skipped as a unit).
            let candidate = [history[i - 1]] + kept
            if tokenCount(head + candidate + tail) > budget { break }
            kept = candidate
            i -= 1
        }
        while let f = kept.first, f.role == "assistant" { kept.removeFirst() }
        return head + kept + tail
    }

    /// History rows → turns for the model: user content and assistant *answers*.
    public static func turns(from rows: [HistoryRow]) -> [PromptTurn] {
        rows.map { PromptTurn(role: $0.role.rawValue, content: $0.content) }
    }
}
