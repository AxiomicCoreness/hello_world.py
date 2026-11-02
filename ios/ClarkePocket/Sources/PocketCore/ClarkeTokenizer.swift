// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// ClarkeEngine part 2: the byte-level BPE tokenizer (GPT-2 / Qwen2 style) built only from the
// GGUF's own metadata: tokenizer.ggml.tokens, tokenizer.ggml.merges, tokenizer.ggml.token_type,
// tokenizer.ggml.eos_token_id. Control / user-defined tokens (<|im_start|>, <|im_end|>, ...) are
// matched as literals before BPE. Foundation only.

import Foundation

public final class ClarkeTokenizer: @unchecked Sendable {
    public let tokens: [String]
    public let eosID: Int32?
    public var bosID: Int32?
    private let ids: [String: Int32]
    private let ranks: [String: Int]          // "left right" -> merge rank
    private let specials: [(String, Int32)]   // longest first
    private let byteEncoder: [Character]      // byte -> printable unicode char
    private let byteDecoder: [Character: UInt8]
    private let pretokenizer: NSRegularExpression
    private var cache: [String: [Int32]] = [:]

    /// Qwen2 pre-tokenizer pattern (llama.cpp LLAMA_VOCAB_PRE_TYPE_QWEN2).
    public static let qwen2Pattern =
        #"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"#

    public init(tokens: [String], merges: [String], tokenTypes: [Int]?, eosID: Int32?) throws {
        self.tokens = tokens
        self.eosID = eosID
        var ids: [String: Int32] = [:]
        ids.reserveCapacity(tokens.count)
        for (i, t) in tokens.enumerated() where ids[t] == nil { ids[t] = Int32(i) }
        self.ids = ids
        var ranks: [String: Int] = [:]
        ranks.reserveCapacity(merges.count)
        for (i, m) in merges.enumerated() where ranks[m] == nil { ranks[m] = i }
        self.ranks = ranks
        var sp: [(String, Int32)] = []
        if let tt = tokenTypes {
            for (i, t) in tt.enumerated() where (t == 3 || t == 4) && i < tokens.count && !tokens[i].isEmpty {
                sp.append((tokens[i], Int32(i)))
            }
        }
        specials = sp.sorted { $0.0.utf8.count > $1.0.utf8.count }
        let enc = Self.bytesToUnicode()
        byteEncoder = enc
        var dec: [Character: UInt8] = [:]
        for (b, c) in enc.enumerated() { dec[c] = UInt8(b) }
        byteDecoder = dec
        pretokenizer = try NSRegularExpression(pattern: Self.qwen2Pattern)
    }

    public convenience init(gguf: GGUFFile) throws {
        guard let toks = gguf.metadata["tokenizer.ggml.tokens"]?.array?.compactMap({ $0.string }), !toks.isEmpty
        else { throw GGUFError.missingKey("tokenizer.ggml.tokens") }
        let merges = gguf.metadata["tokenizer.ggml.merges"]?.array?.compactMap { $0.string } ?? []
        let types = gguf.metadata["tokenizer.ggml.token_type"]?.array?.compactMap { $0.int }
        let eos = gguf.metadata["tokenizer.ggml.eos_token_id"]?.int.map(Int32.init)
        try self.init(tokens: toks, merges: merges, tokenTypes: types, eosID: eos)
        bosID = gguf.metadata["tokenizer.ggml.bos_token_id"]?.int.map(Int32.init)
    }

    public var count: Int { tokens.count }
    public func id(_ token: String) -> Int32? { ids[token] }
    public func isSpecial(_ token: String) -> Bool { specials.contains { $0.0 == token } }

    /// GPT-2 byte <-> unicode table.
    static func bytesToUnicode() -> [Character] {
        var bs: [Int] = Array(33...126) + Array(161...172) + Array(174...255)
        var cs = bs
        var n = 0
        for b in 0..<256 where !bs.contains(b) {
            bs.append(b)
            cs.append(256 + n)
            n += 1
        }
        var table = [Character](repeating: " ", count: 256)
        for (b, c) in zip(bs, cs) { table[b] = Character(Unicode.Scalar(UInt32(c))!) }
        return table
    }

    // MARK: encode

    public func encode(_ text: String) -> [Int32] {
        var out: [Int32] = []
        var rest = Substring(text)
        while !rest.isEmpty {
            // earliest special token
            var best: (range: Range<Substring.Index>, id: Int32)?
            for (s, id) in specials {
                if let r = rest.range(of: s), best == nil || r.lowerBound < best!.range.lowerBound {
                    best = (r, id)
                }
            }
            guard let hit = best else { out += encodeOrdinary(String(rest)); break }
            if hit.range.lowerBound > rest.startIndex { out += encodeOrdinary(String(rest[..<hit.range.lowerBound])) }
            out.append(hit.id)
            rest = rest[hit.range.upperBound...]
        }
        return out
    }

    private func encodeOrdinary(_ text: String) -> [Int32] {
        let ns = text as NSString
        var out: [Int32] = []
        for m in pretokenizer.matches(in: text, range: NSRange(location: 0, length: ns.length)) {
            let piece = ns.substring(with: m.range)
            if let c = cache[piece] { out += c; continue }
            let mapped = String(piece.utf8.map { byteEncoder[Int($0)] })
            let ids = bpe(mapped)
            cache[piece] = ids
            out += ids
        }
        return out
    }

    private func bpe(_ word: String) -> [Int32] {
        if let id = ids[word] { return [id] }
        var parts = word.map { String($0) }
        while parts.count > 1 {
            var bestRank = Int.max, bestAt = -1
            for i in 0..<(parts.count - 1) {
                if let r = ranks[parts[i] + " " + parts[i + 1]], r < bestRank { bestRank = r; bestAt = i }
            }
            if bestAt < 0 { break }
            let (a, b) = (parts[bestAt], parts[bestAt + 1])
            var merged: [String] = []
            merged.reserveCapacity(parts.count)
            var i = 0
            while i < parts.count {
                if i < parts.count - 1 && parts[i] == a && parts[i + 1] == b { merged.append(a + b); i += 2 }
                else { merged.append(parts[i]); i += 1 }
            }
            parts = merged
        }
        var out: [Int32] = []
        for p in parts {
            if let id = ids[p] { out.append(id); continue }
            for ch in p { if let id = ids[String(ch)] { out.append(id) } }   // byte fallback
        }
        return out
    }

    // MARK: decode

    /// Raw bytes for one token (special tokens as their literal text).
    public func bytes(_ id: Int32) -> [UInt8] {
        guard id >= 0, Int(id) < tokens.count else { return [] }
        let t = tokens[Int(id)]
        if specials.contains(where: { $0.1 == id }) { return Array(t.utf8) }
        var out: [UInt8] = []
        for ch in t {
            if let b = byteDecoder[ch] { out.append(b) } else { out += Array(String(ch).utf8) }
        }
        return out
    }

    public func decode(_ ids: [Int32]) -> String {
        String(decoding: ids.flatMap { bytes($0) }, as: UTF8.self)
    }
}

/// Turns a token stream into text pieces without splitting a UTF-8 character.
public struct UTF8PieceBuffer {
    private var pending: [UInt8] = []
    public init() {}
    public mutating func push(_ bytes: [UInt8]) -> String {
        pending += bytes
        // longest valid prefix
        var end = pending.count
        while end > 0 {
            if String(validatingUTF8CString: pending[..<end]) != nil { break }
            end -= 1
            if pending.count - end > 3 { end = pending.count; break }  // invalid, not incomplete: flush
        }
        let out = String(decoding: pending[..<end], as: UTF8.self)
        pending.removeFirst(end)
        return out
    }
}

extension String {
    init?(validatingUTF8CString bytes: ArraySlice<UInt8>) {
        var it = bytes.makeIterator()
        var dec = UTF8()
        var s = ""
        loop: while true {
            switch dec.decode(&it) {
            case .scalarValue(let u): s.unicodeScalars.append(u)
            case .emptyInput: break loop
            case .error: return nil
            }
        }
        self = s
    }
}
