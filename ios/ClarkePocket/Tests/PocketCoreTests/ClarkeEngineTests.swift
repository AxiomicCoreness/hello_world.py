// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// ClarkeEngine, offline. Every GGUF here is a tiny synthetic file written by the test into a temp
// directory (no model weights, no network). Covers: GGUF reader, dequant against hand-computed
// values, BPE round-trip, a 2-layer toy qwen2 forward pass against a naive Swift reference
// (no KV cache, Double accumulation), sampling, ClarkeEngine.run, and syncWithGate offline.

import XCTest
@testable import PocketCore

// MARK: - fixture writer

struct GGUFWriter {
    enum V { case u32(UInt32), f32(Float), str(String), strs([String]), i32s([Int32]), bool(Bool) }
    var kv: [(String, V)] = []
    var tensors: [(name: String, dims: [Int], type: UInt32, bytes: [UInt8])] = []

    static func le<T: FixedWidthInteger>(_ v: T) -> [UInt8] { withUnsafeBytes(of: v.littleEndian) { Array($0) } }
    static func str(_ s: String) -> [UInt8] { le(UInt64(s.utf8.count)) + Array(s.utf8) }

    func bytes(alignment: Int = 32) -> [UInt8] {
        var b: [UInt8] = Array("GGUF".utf8) + Self.le(UInt32(3)) + Self.le(UInt64(tensors.count)) + Self.le(UInt64(kv.count))
        for (k, v) in kv {
            b += Self.str(k)
            switch v {
            case .u32(let x): b += Self.le(UInt32(4)) + Self.le(x)
            case .f32(let x): b += Self.le(UInt32(6)) + Self.le(x.bitPattern)
            case .bool(let x): b += Self.le(UInt32(7)) + [x ? 1 : 0]
            case .str(let s): b += Self.le(UInt32(8)) + Self.str(s)
            case .strs(let a): b += Self.le(UInt32(9)) + Self.le(UInt32(8)) + Self.le(UInt64(a.count)); for s in a { b += Self.str(s) }
            case .i32s(let a): b += Self.le(UInt32(9)) + Self.le(UInt32(5)) + Self.le(UInt64(a.count)); for x in a { b += Self.le(x) }
            }
        }
        var off = 0
        var offsets: [Int] = []
        for t in tensors { offsets.append(off); off += (t.bytes.count + alignment - 1) / alignment * alignment }
        for (t, o) in zip(tensors, offsets) {
            b += Self.str(t.name) + Self.le(UInt32(t.dims.count))
            for d in t.dims { b += Self.le(UInt64(d)) }
            b += Self.le(t.type) + Self.le(UInt64(o))
        }
        while b.count % alignment != 0 { b.append(0) }
        for t in tensors {
            b += t.bytes
            while b.count % alignment != 0 { b.append(0) }
        }
        return b
    }

    func write() throws -> String {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("clarke-\(UUID().uuidString).gguf")
        try Data(bytes()).write(to: url)
        return url.path
    }
}

/// Deterministic pseudo-random numbers for fixtures.
struct FixtureRNG {
    var s: UInt64
    mutating func next() -> UInt64 { s = s &* 6364136223846793005 &+ 1442695040888963407; return s >> 11 }
    mutating func unit() -> Float { Float(next() % 1_000_000) / 1_000_000 }       // [0,1)
    mutating func sym(_ a: Float) -> Float { (unit() * 2 - 1) * a }               // [-a,a)
    mutating func byte() -> UInt8 { UInt8(truncatingIfNeeded: next()) }
}

enum Quant {
    static func h(_ f: Float) -> [UInt8] { GGUFWriter.le(GGMLDequant.floatToHalf(f)) }
    static func f32(_ x: [Float]) -> [UInt8] { x.flatMap { GGUFWriter.le($0.bitPattern) } }
    static func f16(_ x: [Float]) -> [UInt8] { x.flatMap { h($0) } }
    static func q8_0(_ x: [Float]) -> [UInt8] {
        var b: [UInt8] = []
        for blk in stride(from: 0, to: x.count, by: 32) {
            let v = x[blk..<blk + 32]
            let amax = v.map { abs($0) }.max() ?? 0
            let d = amax / 127
            b += h(d)
            for f in v { b.append(UInt8(bitPattern: Int8(d == 0 ? 0 : (f / d).rounded()))) }
        }
        return b
    }
    /// Random but well-scaled Q4_K / Q6_K blocks (the bytes are the weights).
    static func q4K(blocks: Int, _ r: inout FixtureRNG) -> [UInt8] {
        var b: [UInt8] = []
        for _ in 0..<blocks {
            b += h(0.002 + r.unit() * 0.004) + h(0.001 + r.unit() * 0.002)
            for _ in 0..<12 { b.append(r.byte()) }
            for _ in 0..<128 { b.append(r.byte()) }
        }
        return b
    }
    static func q6K(blocks: Int, _ r: inout FixtureRNG) -> [UInt8] {
        var b: [UInt8] = []
        for _ in 0..<blocks {
            for _ in 0..<128 { b.append(r.byte()) }
            for _ in 0..<64 { b.append(r.byte()) }
            for _ in 0..<16 { b.append(UInt8(bitPattern: Int8(Int(r.next() % 31) - 15))) }
            b += h(0.0005 + r.unit() * 0.001)
        }
        return b
    }
}

/// Byte-level vocab: 256 byte tokens, a few merges, ChatML specials.
enum ToyVocab {
    static let merges = ["h e", "l l", "he ll", "hell o"]
    static let specials = ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]
    static var tokens: [String] {
        ClarkeTokenizer.bytesToUnicode().map { String($0) } + ["he", "ll", "hell", "hello"] + specials
    }
    static var types: [Int32] { Array(repeating: 1, count: 260) + [3, 3, 3] }
    static func kv(_ w: inout GGUFWriter) {
        w.kv += [("tokenizer.ggml.model", .str("gpt2")), ("tokenizer.ggml.tokens", .strs(tokens)),
                 ("tokenizer.ggml.merges", .strs(merges)), ("tokenizer.ggml.token_type", .i32s(types)),
                 ("tokenizer.ggml.eos_token_id", .u32(262))]
    }
}

// MARK: - toy model fixture + naive reference

struct ToyModel {
    static let nEmbd = 256, nHead = 4, nKV = 2, nFF = 256, nLayer = 2
    static var nVocab: Int { ToyVocab.tokens.count }

    static func make(tied: Bool, seed: UInt64 = 7) throws -> String {
        var r = FixtureRNG(s: seed)
        var w = GGUFWriter()
        w.kv += [("general.architecture", .str("qwen2")), ("general.alignment", .u32(32)),
                 ("qwen2.block_count", .u32(UInt32(nLayer))), ("qwen2.embedding_length", .u32(UInt32(nEmbd))),
                 ("qwen2.attention.head_count", .u32(UInt32(nHead))), ("qwen2.attention.head_count_kv", .u32(UInt32(nKV))),
                 ("qwen2.feed_forward_length", .u32(UInt32(nFF))), ("qwen2.rope.freq_base", .f32(1_000_000)),
                 ("qwen2.attention.layer_norm_rms_epsilon", .f32(1e-6)), ("qwen2.context_length", .u32(64))]
        ToyVocab.kv(&w)
        func floats(_ n: Int, _ a: Float) -> [Float] { (0..<n).map { _ in r.sym(a) } }
        let kvDim = nKV * (nEmbd / nHead)
        w.tensors.append(("token_embd.weight", [nEmbd, nVocab], 8, Quant.q8_0(floats(nEmbd * nVocab, 1))))
        for l in 0..<nLayer {
            let p = "blk.\(l)."
            w.tensors.append((p + "attn_norm.weight", [nEmbd], 0, Quant.f32((0..<nEmbd).map { _ in 0.8 + r.unit() * 0.4 })))
            w.tensors.append((p + "attn_q.weight", [nEmbd, nEmbd], 12, Quant.q4K(blocks: nEmbd, &r)))
            w.tensors.append((p + "attn_q.bias", [nEmbd], 0, Quant.f32(floats(nEmbd, 0.1))))
            w.tensors.append((p + "attn_k.weight", [nEmbd, kvDim], 14, Quant.q6K(blocks: kvDim, &r)))
            w.tensors.append((p + "attn_k.bias", [kvDim], 0, Quant.f32(floats(kvDim, 0.1))))
            w.tensors.append((p + "attn_v.weight", [nEmbd, kvDim], 1, Quant.f16(floats(nEmbd * kvDim, 0.1))))
            w.tensors.append((p + "attn_v.bias", [kvDim], 0, Quant.f32(floats(kvDim, 0.1))))
            w.tensors.append((p + "attn_output.weight", [nEmbd, nEmbd], 8, Quant.q8_0(floats(nEmbd * nEmbd, 0.1))))
            w.tensors.append((p + "ffn_norm.weight", [nEmbd], 0, Quant.f32((0..<nEmbd).map { _ in 0.8 + r.unit() * 0.4 })))
            w.tensors.append((p + "ffn_gate.weight", [nEmbd, nFF], 12, Quant.q4K(blocks: nFF, &r)))
            w.tensors.append((p + "ffn_up.weight", [nEmbd, nFF], 0, Quant.f32(floats(nEmbd * nFF, 0.1))))
            w.tensors.append((p + "ffn_down.weight", [nFF, nEmbd], 14, Quant.q6K(blocks: nEmbd, &r)))
        }
        w.tensors.append(("output_norm.weight", [nEmbd], 0, Quant.f32((0..<nEmbd).map { _ in 0.8 + r.unit() * 0.4 })))
        if !tied { w.tensors.append(("output.weight", [nEmbd, nVocab], 1, Quant.f16(floats(nEmbd * nVocab, 0.2)))) }
        return try w.write()
    }

    /// Naive reference: recompute every position from scratch, Double accumulation, no cache.
    static func referenceLogits(_ g: GGUFFile, _ toks: [Int32]) throws -> [Double] {
        func m(_ n: String) throws -> (w: [Float], rows: Int, cols: Int) {
            let t = try g.tensor(n); return (t.floats(), t.rows, t.rowLength)
        }
        func mv(_ w: (w: [Float], rows: Int, cols: Int), _ x: [Double]) -> [Double] {
            var y = [Double](repeating: 0, count: w.rows)
            for r in 0..<w.rows { var acc = 0.0; for c in 0..<w.cols { acc += Double(w.w[r * w.cols + c]) * x[c] }; y[r] = acc }
            return y
        }
        func norm(_ x: [Double], _ w: [Float]) -> [Double] {
            let ms = x.reduce(0) { $0 + $1 * $1 } / Double(x.count)
            let s = 1 / (ms + 1e-6).squareRoot()
            return x.enumerated().map { $0.element * s * Double(w[$0.offset]) }
        }
        func rope(_ v: [Double], _ pos: Int, _ hd: Int) -> [Double] {
            var o = v
            for i in 0..<hd / 2 {
                let ang = Double(pos) / pow(1_000_000.0, Double(2 * i) / Double(hd))
                o[i] = v[i] * cos(ang) - v[i + hd / 2] * sin(ang)
                o[i + hd / 2] = v[i + hd / 2] * cos(ang) + v[i] * sin(ang)
            }
            return o
        }
        let hd = nEmbd / nHead
        let emb = try m("token_embd.weight")
        var xs: [[Double]] = toks.map { t in (0..<nEmbd).map { Double(emb.w[Int(t) * nEmbd + $0]) } }
        for l in 0..<nLayer {
            let p = "blk.\(l)."
            let an = try g.tensor(p + "attn_norm.weight").floats(), fn = try g.tensor(p + "ffn_norm.weight").floats()
            let wq = try m(p + "attn_q.weight"), wk = try m(p + "attn_k.weight"), wv = try m(p + "attn_v.weight")
            let bq = try g.tensor(p + "attn_q.bias").floats(), bk = try g.tensor(p + "attn_k.bias").floats(), bv = try g.tensor(p + "attn_v.bias").floats()
            let wo = try m(p + "attn_output.weight"), wg = try m(p + "ffn_gate.weight"), wu = try m(p + "ffn_up.weight"), wd = try m(p + "ffn_down.weight")
            var Q: [[Double]] = [], K: [[Double]] = [], Vv: [[Double]] = []
            for (pos, x) in xs.enumerated() {
                let h = norm(x, an)
                var q = mv(wq, h), k = mv(wk, h), v = mv(wv, h)
                for i in q.indices { q[i] += Double(bq[i]) }
                for i in k.indices { k[i] += Double(bk[i]) }
                for i in v.indices { v[i] += Double(bv[i]) }
                Q.append((0..<nHead).flatMap { rope(Array(q[$0 * hd..<($0 + 1) * hd]), pos, hd) })
                K.append((0..<nKV).flatMap { rope(Array(k[$0 * hd..<($0 + 1) * hd]), pos, hd) })
                Vv.append(v)
            }
            var out: [[Double]] = []
            for pos in xs.indices {
                var a = [Double](repeating: 0, count: nEmbd)
                for head in 0..<nHead {
                    let kvh = head / (nHead / nKV)
                    var sc: [Double] = []
                    for t in 0...pos {
                        var d = 0.0
                        for j in 0..<hd { d += Q[pos][head * hd + j] * K[t][kvh * hd + j] }
                        sc.append(d / Double(hd).squareRoot())
                    }
                    let mx = sc.max()!
                    sc = sc.map { exp($0 - mx) }
                    let s = sc.reduce(0, +)
                    for t in 0...pos { for j in 0..<hd { a[head * hd + j] += sc[t] / s * Vv[t][kvh * hd + j] } }
                }
                var x = xs[pos]
                let o = mv(wo, a)
                for i in x.indices { x[i] += o[i] }
                let h2 = norm(x, fn)
                let gg = mv(wg, h2), uu = mv(wu, h2)
                let act = zip(gg, uu).map { ($0 / (1 + exp(-$0))) * $1 }
                let d = mv(wd, act)
                for i in x.indices { x[i] += d[i] }
                out.append(x)
            }
            xs = out
        }
        let on = try g.tensor("output_norm.weight").floats()
        let outW = try m(g.tensors["output.weight"] != nil ? "output.weight" : "token_embd.weight")
        return mv(outW, norm(xs.last!, on))
    }
}

// MARK: - tests

final class ClarkeEngineTests: XCTestCase {

    func testGGUFReaderHeaderMetadataAndTensorIndex() throws {
        var w = GGUFWriter()
        w.kv = [("general.architecture", .str("qwen2")), ("a.u32", .u32(7)), ("a.f32", .f32(0.5)),
                ("a.bool", .bool(true)), ("a.strs", .strs(["x", "yz"]))]
        w.tensors = [("t0", [4, 2], 0, Quant.f32([1, 2, 3, 4, 5, 6, 7, 8])), ("t1", [32], 8, Quant.q8_0((0..<32).map { Float($0) }))]
        let g = try GGUFFile(path: try w.write())
        XCTAssertEqual(g.version, 3)
        XCTAssertEqual(g.string("general.architecture"), "qwen2")
        XCTAssertEqual(g.metadata["a.u32"]?.int, 7)
        XCTAssertEqual(g.double("a.f32"), 0.5)
        XCTAssertEqual(g.metadata["a.bool"], .bool(true))
        XCTAssertEqual(g.metadata["a.strs"]?.array?.compactMap { $0.string }, ["x", "yz"])
        XCTAssertEqual(g.tensorOrder, ["t0", "t1"])
        XCTAssertEqual(g.dataOffset % 32, 0)
        let t0 = try g.tensor("t0")
        XCTAssertEqual(t0.rows, 2); XCTAssertEqual(t0.rowLength, 4)
        XCTAssertEqual(t0.row(1), [5, 6, 7, 8])
        XCTAssertEqual(g.tensors["t1"]?.offset, 32)
        XCTAssertThrowsError(try g.tensor("nope"))

        var bad = w.bytes(); bad[0] = 0x58
        let badURL = FileManager.default.temporaryDirectory.appendingPathComponent("bad-\(UUID().uuidString).gguf")
        try Data(bad).write(to: badURL)
        XCTAssertThrowsError(try GGUFFile(path: badURL.path)) { XCTAssertEqual($0 as? GGUFError, .badMagic) }
        try Data(w.bytes().prefix(40)).write(to: badURL)
        XCTAssertThrowsError(try GGUFFile(path: badURL.path))
    }

    func testHalfFloatConversions() {
        XCTAssertEqual(GGMLDequant.halfToFloat(0x3C00), 1)
        XCTAssertEqual(GGMLDequant.halfToFloat(0xC000), -2)
        XCTAssertEqual(GGMLDequant.halfToFloat(0x7BFF), 65504)
        XCTAssertEqual(GGMLDequant.halfToFloat(0x0001), 5.9604645e-08)
        XCTAssertEqual(GGMLDequant.halfToFloat(0x3800), 0.5)
        for f: Float in [0, 1, -2, 0.5, 0.25, 65504, 0.1, -3.140625] {
            XCTAssertEqual(GGMLDequant.halfToFloat(GGMLDequant.floatToHalf(f)), f, accuracy: abs(f) * 1e-3)
        }
    }

    private func deq(_ type: GGMLType, _ bytes: [UInt8], _ n: Int) -> [Float] {
        var out = [Float](repeating: 0, count: n)
        bytes.withUnsafeBytes { src in out.withUnsafeMutableBufferPointer { GGMLDequant.row(type, src.baseAddress!, n, $0.baseAddress!) } }
        return out
    }

    func testDequantQ8_0F16F32Q5_0() {
        let q8: [UInt8] = Quant.h(0.5) + (0..<32).map { UInt8(bitPattern: Int8($0 - 16)) }
        XCTAssertEqual(deq(.q8_0, q8, 32), (0..<32).map { Float($0 - 16) * 0.5 })
        XCTAssertEqual(deq(.f16, Quant.f16([1, -2, 0.5]), 3), [1, -2, 0.5])
        XCTAssertEqual(deq(.f32, Quant.f32([3.25, -1]), 2), [3.25, -1])
        // Q5_0: d = 1, qh bit j sets the 5th bit of element j; qs = 0x21 -> low nibble 1, high 2.
        let q5 = Quant.h(1) + GGUFWriter.le(UInt32(0x0001_0001)) + [UInt8](repeating: 0x21, count: 16)
        let y = deq(.q5_0, q5, 32)
        XCTAssertEqual(y[0], Float((1 | 16) - 16))    // bit 0 -> element 0
        XCTAssertEqual(y[1], Float(1 - 16))
        XCTAssertEqual(y[16], Float((2 | 16) - 16))   // bit 16 -> element 16 (ggml: qh >> (j + 12) & 0x10)
        XCTAssertEqual(y[20], Float(2 - 16))
    }

    func testDequantQ4K() {
        // d = 1, dmin = 0.5; scales: sc = [1,2,3,4, 17,3,5,7], m = [5,6,7,8, 2,4,6,8]
        let scales: [UInt8] = [1 | 0x40, 2, 3, 4, 5, 6, 7, 8, 0x21, 0x43, 0x65, 0x87]
        let qs: [UInt8] = (0..<128).map { UInt8($0) }
        let y = deq(.q4_K, Quant.h(1) + Quant.h(0.5) + scales + qs, 256)
        let sc: [Float] = [1, 2, 3, 4, 17, 3, 5, 7], mn: [Float] = [5, 6, 7, 8, 2, 4, 6, 8]
        for c in 0..<4 {
            for l in 0..<32 {
                let q = qs[32 * c + l]
                XCTAssertEqual(y[64 * c + l], sc[2 * c] * Float(q & 0xF) - 0.5 * mn[2 * c])
                XCTAssertEqual(y[64 * c + 32 + l], sc[2 * c + 1] * Float(q >> 4) - 0.5 * mn[2 * c + 1])
            }
        }
        XCTAssertEqual(y[0], -2.5)       // 1*0 - 0.5*5
        XCTAssertEqual(y[33], -3)        // 2*(1>>4) - 0.5*6
        XCTAssertEqual(y[69], 11.5)      // c=1: 3*(37&15) - 0.5*7
        XCTAssertEqual(y[128 + 2], 17 * 2 - 1)   // c=2 uses the 6-bit high scale 17, m 2
    }

    func testDequantQ6K() {
        let ql: [UInt8] = (0..<128).map { UInt8($0) }
        let qh = [UInt8](repeating: 0xE4, count: 64)          // 2-bit groups 0,1,2,3
        let sc: [UInt8] = (0..<16).map { UInt8(bitPattern: Int8($0 - 8)) }
        let y = deq(.q6_K, ql + qh + sc + Quant.h(0.25), 256)
        XCTAssertEqual(y[0], 64)        // q=0|0<<4 -> -32; sc -8; 0.25*-8*-32
        XCTAssertEqual(y[40], 12)       // ql[40]&15=8 | 1<<4 = 24 -> -8; sc[2]=-6
        XCTAssertEqual(y[64], 0.25 * -4 * Float((0 >> 4 | 2 << 4) - 32))   // q3, sc[4]=-4
        XCTAssertEqual(y[96 + 17], 0.25 * -1 * Float((49 >> 4 | 3 << 4) - 32))  // q4 l=17: is=1, sc[7]=-1
        XCTAssertEqual(y[128], 0.25 * 0 * -32)   // second half uses ql[64...], sc[8]=0
        XCTAssertEqual(y[128 + 1], 0)
        XCTAssertEqual(y[128 + 16], 0.25 * 1 * Float((80 & 15) - 32))   // ql[64+16]=80, sc[9]=1
    }

    func testTokenizerRoundTripAndSpecials() throws {
        var w = GGUFWriter(); ToyVocab.kv(&w)
        let tok = try ClarkeTokenizer(gguf: GGUFFile(path: w.write()))
        let hello = tok.id("hello")!
        XCTAssertEqual(tok.encode("hello"), [hello])
        let s = "<|im_start|>user\nhello world<|im_end|>\n"
        let ids = tok.encode(s)
        XCTAssertEqual(ids.first, tok.id("<|im_start|>"))
        XCTAssertTrue(ids.contains(hello))
        XCTAssertTrue(ids.contains(tok.id("<|im_end|>")!))
        XCTAssertEqual(tok.decode(ids), s)
        for text in ["héllo wörld ✓ 123", "  spaces\n\n\ttabs", "emoji 🙂 and 中文", ""] {
            XCTAssertEqual(tok.decode(tok.encode(text)), text)
        }
        // Streaming: a 4-byte emoji split across tokens is emitted whole.
        var buf = UTF8PieceBuffer()
        var out = ""
        for id in tok.encode("a🙂b") { out += buf.push(tok.bytes(id)) }
        XCTAssertEqual(out, "a🙂b")
    }

    func testToyForwardMatchesNaiveReference() throws {
        for tied in [false, true] {
            let path = try ToyModel.make(tied: tied)
            let g = try GGUFFile(path: path)
            let model = try Qwen2Model(gguf: g, fallback: ClarkeEngine.config, nCtx: 32)
            XCTAssertEqual(model.tiedOutput, tied)
            XCTAssertEqual(model.hp.nLayer, 2); XCTAssertEqual(model.hp.headDim, 64); XCTAssertEqual(model.hp.ropeBase, 1_000_000)
            let toks: [Int32] = [5, 260, 72, 101]
            for n in 1...toks.count {
                let got = try model.forward(token: toks[n - 1])
                let want = try ToyModel.referenceLogits(g, Array(toks[..<n]))
                XCTAssertEqual(got.count, ToyModel.nVocab)
                let scale = want.map { abs($0) }.max()!
                let err = zip(got, want).map { abs(Double($0) - $1) }.max()!
                XCTAssertLessThan(err, 1e-4 * max(scale, 1), "tied \(tied) step \(n): max err \(err), scale \(scale)")
                XCTAssertEqual(got.indices.max { got[$0] < got[$1] }, want.indices.max { want[$0] < want[$1] })
            }
        }
    }

    func testSamplerGreedyAndSeeded() {
        let logits: [Float] = [0.1, 3, -1, 2.9]
        var g = ClarkeSampler(temperature: 0, seed: 1)
        XCTAssertEqual(g.sample(logits), 1)
        var a = ClarkeSampler(temperature: 1, seed: 42), b = ClarkeSampler(temperature: 1, seed: 42)
        let sa = (0..<50).map { _ in a.sample(logits) }, sb = (0..<50).map { _ in b.sample(logits) }
        XCTAssertEqual(sa, sb)
        XCTAssertTrue(Set(sa).isSubset(of: [0, 1, 2, 3]))
        XCTAssertTrue(sa.contains(3), "temperature 1 should sometimes pick the 2.9 logit")
    }

    func testRunGeneratesRealTokensAndReportsResults() throws {
        let path = try ToyModel.make(tied: false)
        ClarkeEngine.contextTokens = 64
        let r = try ClarkeEngine.run(modelPath: path, user: "hello", maxTokens: 5, temperature: 0)
        XCTAssertEqual(r.engineName, ClarkeEngine.engineName)
        XCTAssertEqual(r.modelSHA256, ClarkeEngine.pinnedModel.sha256)
        XCTAssertEqual(r.modelSHA256.count, 64)
        XCTAssertFalse(r.modelSizeMatchesPin)   // toy file, not the pinned GGUF
        XCTAssertGreaterThan(r.promptTokens, 4)
        XCTAssertGreaterThan(r.tokens.count, 0)
        XCTAssertLessThanOrEqual(r.tokens.count, 5)
        XCTAssertGreaterThan(r.tokensPerSecond, 0)  // measured on whatever machine runs the test

        // Greedy first token equals the naive reference's argmax over the same prompt.
        let s = try ClarkeEngine.Session(modelPath: path, nCtx: 64)
        let prompt = s.tokenizer.encode(s.render([PromptTurn(role: "system", content: ""), PromptTurn(role: "user", content: "hello")]))
        XCTAssertEqual(ClarkeEngine.Session.format(for: s.tokenizer), .chatML)
        let want = try ToyModel.referenceLogits(GGUFFile(path: path), prompt)
        XCTAssertEqual(Int(r.tokens[0]), want.indices.max { want[$0] < want[$1] })
        XCTAssertEqual(ClarkeEngine.config.nEmbd, ToyModel.nEmbd)   // read from the model
        ClarkeEngine.config = Qwen2Hyperparameters(nLayer: 28, nEmbd: 1536, nHead: 12, nHeadKV: 2, nFF: 8960,
                                                   ropeBase: 1_000_000, rmsEps: 1e-6, nVocab: 151_936, nCtxTrain: 131_072)
        ClarkeEngine.contextTokens = 2048
    }

    func testSyncWithGateOfflineDefaultsAndValidation() async throws {
        let before = ClarkeEngine.pinnedModel
        XCTAssertEqual(before.sha256, ModelPin.sha256)
        XCTAssertEqual(before.name, ModelPin.fileName)
        XCTAssertThrowsError(try ClarkeEngine.manifestURL(base: URL(string: "http://example.com")!))
        XCTAssertEqual(try ClarkeEngine.manifestURL(base: URL(string: "https://gate.example")!).absoluteString,
                       "https://gate.example/clarke-engine/model-manifest.json")
        // Nothing listens on 127.0.0.1:9 in CI: offline -> defaults kept.
        let r = try await ClarkeEngine.syncWithGate(base: URL(string: "http://127.0.0.1:9")!)
        guard case .offlineDefaults = r else { return XCTFail("expected offline defaults, got \(r)") }
        XCTAssertEqual(ClarkeEngine.pinnedModel, before)

        let good = #"{"name":"x.gguf","sha256":"\#(String(repeating: "A", count: 64))","size_bytes":5}"#
        let m = try JSONDecoder().decode(ClarkeEngine.ModelManifest.self, from: Data(good.utf8)).validated()
        XCTAssertEqual(m.sha256, String(repeating: "a", count: 64))
        for bad in [#"{"name":"x.bin","sha256":"\#(String(repeating: "a", count: 64))","size_bytes":5}"#,
                    #"{"name":"x.gguf","sha256":"abc","size_bytes":5}"#,
                    #"{"name":"../x.gguf","sha256":"\#(String(repeating: "a", count: 64))","size_bytes":5}"#,
                    #"{"name":"x.gguf","sha256":"\#(String(repeating: "a", count: 64))","size_bytes":0}"#] {
            XCTAssertThrowsError(try JSONDecoder().decode(ClarkeEngine.ModelManifest.self, from: Data(bad.utf8)).validated())
        }
    }
}
