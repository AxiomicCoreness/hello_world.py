// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// How much memory iOS will still give this app before jetsam, and the P-core count for threads.

import Foundation
import os

enum MemoryMonitor {
    /// `os_proc_available_memory()` (iOS 13+): bytes this process can still allocate. 0 = unknown.
    static func availableBytes() -> Int64 {
        Int64(os_proc_available_memory())
    }

    /// Performance cores (A14 Bionic: 2). nil if the kernel does not say.
    static func performanceCores() -> Int? {
        var n: Int32 = 0
        var size = MemoryLayout<Int32>.size
        guard sysctlbyname("hw.perflevel0.physicalcpu", &n, &size, nil, 0) == 0, n > 0 else { return nil }
        return Int(n)
    }

    static func threads() -> (gen: Int32, batch: Int32) {
        RuntimePolicy.threads(performanceCores: performanceCores(),
                              totalCores: ProcessInfo.processInfo.activeProcessorCount)
    }
}
