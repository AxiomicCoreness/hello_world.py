// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// ClarkeEngine part 3: a pure-Swift qwen2 decoder over the GGUF tensors.
//   RMSNorm -> Q/K/V (with biases) -> RoPE (NEOX, base from the model) -> GQA attention over a
//   KV cache -> output projection -> residual; RMSNorm -> SwiGLU MLP -> residual; final RMSNorm ->
//   logits (output.weight, or the tied token_embd.weight). CPU only: Accelerate (vDSP) on Apple
//   platforms, plain loops elsewhere. Rows are dequantised on the fly, so the weights stay
//   quantised in the mmap'd file.

import Foundation
#if canImport(Accelerate)
import Accelerate
#endif

public struct Qwen2Hyperparameters: Equatable, Sendable {
    public var nLayer: Int
    public var nEmbd: Int
    public var nHead: Int
    public var nHeadKV: Int
    public var nFF: Int
    public var ropeBase: Double
    public var rmsEps: Double
    public var nVocab: Int
    public var nCtxTrain: Int
    public var headDim: Int { nEmbd / nHead }

    public init(nLayer: Int, nEmbd: Int, nHead: Int, nHeadKV: Int, nFF: Int,
                ropeBase: Double, rmsEps: Double, nVocab: Int, nCtxTrain: Int) {
        self.nLayer = nLayer; self.nEmbd = nEmbd; self.nHead = nHead; self.nHeadKV = nHeadKV
        self.nFF = nFF; self.ropeBase = ropeBase; self.rmsEps = rmsEps; self.nVocab = nVocab
        self.nCtxTrain = nCtxTrain
    }

    /// Read from GGUF metadata (`<arch>.*`); `fallback` fills keys the file leaves out.
    public static func read(_ g: GGUFFile, fallback: Qwen2Hyperparameters) throws -> Qwen2Hyperparameters {
        let arch = g.string("general.architecture") ?? "qwen2"
        func i(_ k: String, _ d: Int) -> Int { g.metadata["\(arch).\(k)"]?.int ?? d }
        func f(_ k: String, _ d: Double) -> Double { g.metadata["\(arch).\(k)"]?.double ?? d }
        let vocab = g.metadata["tokenizer.ggml.tokens"]?.array?.count ?? fallback.nVocab
        let hp = Qwen2Hyperparameters(
            nLayer: try g.int("\(arch).block_count"),
            nEmbd: try g.int("\(arch).embedding_length"),
            nHead: try g.int("\(arch).attention.head_count"),
            nHeadKV: i("attention.head_count_kv", fallback.nHeadKV),
            nFF: i("feed_forward_length", fallback.nFF),
            ropeBase: f("rope.freq_base", fallback.ropeBase),
            rmsEps: f("attention.layer_norm_rms_epsilon", fallback.rmsEps),
            nVocab: vocab,
            nCtxTrain: i("context_length", fallback.nCtxTrain))
        guard hp.nHead > 0, hp.nHeadKV > 0, hp.nEmbd % hp.nHead == 0, hp.nHead % hp.nHeadKV == 0,
              hp.headDim % 2 == 0 else { throw GGUFError.shape("bad head layout \(hp)") }
        return hp
    }
}

/// Small vector kernels (vDSP when available).
public enum ClarkeMath {
    @inline(__always)
    public static func dot(_ a: UnsafePointer<Float>, _ b: UnsafePointer<Float>, _ n: Int) -> Float {
        #if canImport(Accelerate)
        var r: Float = 0
        vDSP_dotpr(a, 1, b, 1, &r, vDSP_Length(n))
        return r
        #else
        var s0: Float = 0, s1: Float = 0, s2: Float = 0, s3: Float = 0
        var i = 0
        while i + 4 <= n { s0 += a[i] * b[i]; s1 += a[i+1] * b[i+1]; s2 += a[i+2] * b[i+2]; s3 += a[i+3] * b[i+3]; i += 4 }
        while i < n { s0 += a[i] * b[i]; i += 1 }
        return (s0 + s1) + (s2 + s3)
        #endif
    }

    public static func rmsNorm(_ x: [Float], _ w: [Float], eps: Float) -> [Float] {
        var ss: Float = 0
        for v in x { ss += v * v }
        let scale = 1 / (ss / Float(x.count) + eps).squareRoot()
        var out = [Float](repeating: 0, count: x.count)
        for i in 0..<x.count { out[i] = x[i] * scale * w[i] }
        return out
    }

    /// In-place softmax over the first `n` values.
    public static func softmax(_ x: inout [Float], _ n: Int) {
        var m = -Float.infinity
        for i in 0..<n where x[i] > m { m = x[i] }
        var s: Float = 0
        for i in 0..<n { x[i] = expf(x[i] - m); s += x[i] }
        for i in 0..<n { x[i] /= s }
    }

    /// NEOX rotary embedding on one head (pairs i and i + d/2).
    public static func ropeNeox(_ v: UnsafeMutablePointer<Float>, headDim d: Int, pos: Int, base: Double) {
        let half = d / 2
        for i in 0..<half {
            let theta = Double(pos) * pow(base, -2.0 * Double(i) / Double(d))
            let c = Float(cos(theta)), s = Float(sin(theta))
            let a = v[i], b = v[i + half]
            v[i] = a * c - b * s
            v[i + half] = a * s + b * c
        }
    }

    @inline(__always) public static func silu(_ x: Float) -> Float { x / (1 + expf(-x)) }

    /// y = W x for a GGUF tensor W (rows = outputs, rowLength = inputs). Rows are dequantised on
    /// the fly into per-chunk scratch; chunks run in parallel.
    public static func matvec(_ w: GGUFTensor, _ x: [Float]) -> [Float] {
        let n = w.rowLength, rows = w.rows
        precondition(x.count == n, "matvec \(w.info.name): \(x.count) != \(n)")
        var y = [Float](repeating: 0, count: rows)
        let chunks = Swift.min(rows, Swift.max(1, ProcessInfo.processInfo.activeProcessorCount * 4))
        let per = (rows + chunks - 1) / chunks
        x.withUnsafeBufferPointer { xb in
            y.withUnsafeMutableBufferPointer { yb in
                let xp = xb.baseAddress!, yp = yb.baseAddress!
                DispatchQueue.concurrentPerform(iterations: chunks) { c in
                    let lo = c * per, hi = Swift.min(rows, lo + per)
                    guard lo < hi else { return }
                    let scratch = UnsafeMutablePointer<Float>.allocate(capacity: n)
                    defer { scratch.deallocate() }
                    for r in lo..<hi {
                        w.row(r, into: scratch)
                        yp[r] = dot(scratch, xp, n)
                    }
                }
            }
        }
        return y
    }
}

/// The loaded model plus its KV cache. Not thread-safe: one sequence at a time.
public final class Qwen2Model: @unchecked Sendable {
    public let gguf: GGUFFile
    public let hp: Qwen2Hyperparameters
    public let nCtx: Int

    struct Layer {
        let attnNorm: [Float], ffnNorm: [Float]
        let wq: GGUFTensor, wk: GGUFTensor, wv: GGUFTensor, wo: GGUFTensor
        let bq: [Float]?, bk: [Float]?, bv: [Float]?
        let gate: GGUFTensor, up: GGUFTensor, down: GGUFTensor
    }
    let tokEmbd: GGUFTensor
    let outNorm: [Float]
    let output: GGUFTensor   // output.weight, or token_embd.weight when tied
    public let tiedOutput: Bool
    let layers: [Layer]

    // KV cache: [layer][pos * kvDim + j]
    private var kCache: [[Float]]
    private var vCache: [[Float]]
    public private(set) var nPast = 0

    public init(gguf: GGUFFile, fallback: Qwen2Hyperparameters, nCtx: Int = 2048) throws {
        self.gguf = gguf
        let hp = try Qwen2Hyperparameters.read(gguf, fallback: fallback)
        self.hp = hp
        self.nCtx = Swift.max(8, Swift.min(nCtx, hp.nCtxTrain > 0 ? hp.nCtxTrain : nCtx))
        tokEmbd = try gguf.tensor("token_embd.weight")
        guard tokEmbd.rowLength == hp.nEmbd else { throw GGUFError.shape("token_embd row \(tokEmbd.rowLength) != n_embd \(hp.nEmbd)") }
        outNorm = try gguf.tensor("output_norm.weight").floats()
        if gguf.tensors["output.weight"] != nil {
            output = try gguf.tensor("output.weight"); tiedOutput = false
        } else {
            output = tokEmbd; tiedOutput = true
        }
        let kvDim = hp.nHeadKV * hp.headDim
        var ls: [Layer] = []
        for i in 0..<hp.nLayer {
            func t(_ n: String) throws -> GGUFTensor { try gguf.tensor("blk.\(i).\(n)") }
            func opt(_ n: String) throws -> [Float]? {
                gguf.tensors["blk.\(i).\(n)"] == nil ? nil : try t(n).floats()
            }
            let l = Layer(attnNorm: try t("attn_norm.weight").floats(), ffnNorm: try t("ffn_norm.weight").floats(),
                          wq: try t("attn_q.weight"), wk: try t("attn_k.weight"), wv: try t("attn_v.weight"),
                          wo: try t("attn_output.weight"),
                          bq: try opt("attn_q.bias"), bk: try opt("attn_k.bias"), bv: try opt("attn_v.bias"),
                          gate: try t("ffn_gate.weight"), up: try t("ffn_up.weight"), down: try t("ffn_down.weight"))
            guard l.wq.rows == hp.nEmbd, l.wk.rows == kvDim, l.wv.rows == kvDim, l.wo.rowLength == hp.nEmbd,
                  l.gate.rows == hp.nFF, l.down.rowLength == hp.nFF
            else { throw GGUFError.shape("layer \(i) does not match n_embd/n_head_kv/n_ff") }
            ls.append(l)
        }
        layers = ls
        kCache = Array(repeating: [], count: hp.nLayer)
        vCache = Array(repeating: [], count: hp.nLayer)
    }

    public func reset() { nPast = 0 }

    /// Feed one token at position `nPast`; returns the logits for the next token.
    public func forward(token: Int32) throws -> [Float] {
        guard token >= 0, Int(token) < tokEmbd.rows else { throw GGUFError.shape("token \(token) out of vocab") }
        guard nPast < nCtx else { throw GGUFError.shape("context full (\(nCtx) tokens)") }
        let hd = hp.headDim, nh = hp.nHead, nkv = hp.nHeadKV, kvDim = nkv * hd
        let group = nh / nkv
        let pos = nPast
        let eps = Float(hp.rmsEps)
        var x = tokEmbd.row(Int(token))
        for (li, L) in layers.enumerated() {
            if kCache[li].count < (pos + 1) * kvDim {
                let grow = Swift.min(nCtx, Swift.max(pos + 1, Swift.max(64, kCache[li].count / kvDim * 2))) * kvDim
                kCache[li] += [Float](repeating: 0, count: grow - kCache[li].count)
                vCache[li] += [Float](repeating: 0, count: grow - vCache[li].count)
            }
            let h = ClarkeMath.rmsNorm(x, L.attnNorm, eps: eps)
            var q = ClarkeMath.matvec(L.wq, h)
            var k = ClarkeMath.matvec(L.wk, h)
            var v = ClarkeMath.matvec(L.wv, h)
            if let b = L.bq { for j in 0..<q.count { q[j] += b[j] } }
            if let b = L.bk { for j in 0..<k.count { k[j] += b[j] } }
            if let b = L.bv { for j in 0..<v.count { v[j] += b[j] } }
            q.withUnsafeMutableBufferPointer { p in
                for hh in 0..<nh { ClarkeMath.ropeNeox(p.baseAddress! + hh * hd, headDim: hd, pos: pos, base: hp.ropeBase) }
            }
            k.withUnsafeMutableBufferPointer { p in
                for hh in 0..<nkv { ClarkeMath.ropeNeox(p.baseAddress! + hh * hd, headDim: hd, pos: pos, base: hp.ropeBase) }
            }
            for j in 0..<kvDim { kCache[li][pos * kvDim + j] = k[j]; vCache[li][pos * kvDim + j] = v[j] }

            var attn = [Float](repeating: 0, count: nh * hd)
            let scale = 1 / Float(hd).squareRoot()
            var scores = [Float](repeating: 0, count: pos + 1)
            kCache[li].withUnsafeBufferPointer { kc in
                vCache[li].withUnsafeBufferPointer { vc in
                    q.withUnsafeBufferPointer { qb in
                        for hh in 0..<nh {
                            let kvh = hh / group
                            let qp = qb.baseAddress! + hh * hd
                            for t in 0...pos { scores[t] = ClarkeMath.dot(qp, kc.baseAddress! + t * kvDim + kvh * hd, hd) * scale }
                            ClarkeMath.softmax(&scores, pos + 1)
                            for t in 0...pos {
                                let p = scores[t], vp = vc.baseAddress! + t * kvDim + kvh * hd
                                for j in 0..<hd { attn[hh * hd + j] += p * vp[j] }
                            }
                        }
                    }
                }
            }
            let o = ClarkeMath.matvec(L.wo, attn)
            for j in 0..<x.count { x[j] += o[j] }

            let h2 = ClarkeMath.rmsNorm(x, L.ffnNorm, eps: eps)
            let g = ClarkeMath.matvec(L.gate, h2)
            let u = ClarkeMath.matvec(L.up, h2)
            var a = [Float](repeating: 0, count: g.count)
            for j in 0..<g.count { a[j] = ClarkeMath.silu(g[j]) * u[j] }
            let d = ClarkeMath.matvec(L.down, a)
            for j in 0..<x.count { x[j] += d[j] }
        }
        nPast += 1
        let xn = ClarkeMath.rmsNorm(x, outNorm, eps: eps)
        return ClarkeMath.matvec(output, xn)
    }
}

/// Greedy (temperature <= 0) or temperature sampling. No filtering of any token.
public struct ClarkeSampler {
    public var temperature: Float
    private var state: UInt64

    public init(temperature: Float, seed: UInt64) {
        self.temperature = temperature
        self.state = seed &+ 0x9E37_79B9_7F4A_7C15
    }

    /// SplitMix64, so runs are reproducible for a seed.
    mutating func nextUnit() -> Double {
        state &+= 0x9E37_79B9_7F4A_7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58_476D_1CE4_E5B9
        z = (z ^ (z >> 27)) &* 0x94D0_49BB_1331_11EB
        z ^= z >> 31
        return Double(z >> 11) / Double(1 << 53)
    }

    public mutating func sample(_ logits: [Float]) -> Int32 {
        var best = 0
        for i in 1..<logits.count where logits[i] > logits[best] { best = i }
        if temperature <= 0 { return Int32(best) }
        var p = logits.map { $0 / temperature }
        ClarkeMath.softmax(&p, p.count)
        let r = nextUnit()
        var acc = 0.0
        for i in 0..<p.count {
            acc += Double(p[i])
            if r < acc { return Int32(i) }
        }
        return Int32(best)   // rounding left r just above the total
    }
}
