// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// llama.cpp hands out token pieces as raw bytes, and one character (é, φ, 😀, CJK) is often split
// across two or more tokens. This buffers bytes and releases only complete UTF-8 characters, so
// the streaming chat never shows "�" halfway through a word. Invalid bytes become U+FFFD.

import Foundation

public struct UTF8Assembler: Sendable {
    private var pending: [UInt8] = []

    public init() {}

    /// Add bytes; returns the text that is now complete (possibly "").
    public mutating func push<S: Sequence>(_ bytes: S) -> String where S.Element == UInt8 {
        pending.append(contentsOf: bytes)
        let cut = Self.completePrefixLength(pending)
        guard cut > 0 else { return "" }
        let out = String(decoding: pending[..<cut], as: UTF8.self)
        pending.removeFirst(cut)
        return out
    }

    /// Whatever is left at the end of generation (an incomplete tail decodes as U+FFFD).
    public mutating func flush() -> String {
        defer { pending.removeAll() }
        return pending.isEmpty ? "" : String(decoding: pending, as: UTF8.self)
    }

    /// Length of the longest prefix that does not end inside a still-possible multi-byte sequence.
    static func completePrefixLength(_ b: [UInt8]) -> Int {
        let n = b.count
        // Look at most 3 bytes back for the start of the last sequence.
        var i = n - 1
        var back = 0
        while i >= 0 && back < 4 {
            let c = b[i]
            if c & 0xC0 != 0x80 {   // a lead byte or ASCII
                let need: Int
                if c < 0x80 { need = 1 }
                else if c & 0xE0 == 0xC0 { need = 2 }
                else if c & 0xF0 == 0xE0 { need = 3 }
                else if c & 0xF8 == 0xF0 { need = 4 }
                else { return n }       // invalid lead byte: release everything (decodes to U+FFFD)
                return (n - i) >= need ? n : i
            }
            i -= 1
            back += 1
        }
        return n   // only continuation bytes: invalid, release them
    }
}
