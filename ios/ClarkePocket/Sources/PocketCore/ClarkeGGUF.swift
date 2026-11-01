// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// ClarkeEngine part 1: a GGUF reader (header, KV metadata, tensor index) over an mmap'd file, and
// ggml dequantisation for F32 / F16 / Q8_0 / Q4_K / Q6_K (plus Q5_0, which llama.cpp uses for
// rows that are not a multiple of 256). Foundation only. Layouts follow ggml-quants.c.

import Foundation
#if canImport(Darwin)
import Darwin
#elseif canImport(Glibc)
import Glibc
#endif

public enum GGUFError: Error, Equatable, CustomStringConvertible {
    case open(String)
    case badMagic
    case unsupportedVersion(UInt32)
    case truncated(String)
    case badValueType(UInt32)
    case missingKey(String)
    case missingTensor(String)
    case unsupportedTensorType(String, UInt32)
    case shape(String)

    public var description: String {
        switch self {
        case .open(let p): return "cannot open \(p)"
        case .badMagic: return "not a GGUF file"
        case .unsupportedVersion(let v): return "GGUF version \(v) not supported"
        case .truncated(let w): return "GGUF truncated (\(w))"
        case .badValueType(let t): return "GGUF value type \(t) unknown"
        case .missingKey(let k): return "GGUF metadata key \(k) missing"
        case .missingTensor(let n): return "tensor \(n) missing"
        case .unsupportedTensorType(let n, let t): return "tensor \(n) has ggml type \(t), which ClarkeEngine does not dequantise"
        case .shape(let w): return "tensor shape: \(w)"
        }
    }
}

/// ggml tensor types ClarkeEngine reads.
public enum GGMLType: UInt32, Sendable {
    case f32 = 0, f16 = 1, q5_0 = 6, q8_0 = 8, q4_K = 12, q6_K = 14

    /// (elements per block, bytes per block)
    public var block: (n: Int, bytes: Int) {
        switch self {
        case .f32: return (1, 4)
        case .f16: return (1, 2)
        case .q5_0: return (32, 22)
        case .q8_0: return (32, 34)
        case .q4_K: return (256, 144)
        case .q6_K: return (256, 210)
        }
    }
    public func rowBytes(_ n: Int) -> Int { n / block.n * block.bytes }
}

public enum GGUFValue: Equatable, Sendable {
    case int(Int64)
    case uint(UInt64)
    case float(Double)
    case bool(Bool)
    case string(String)
    case array([GGUFValue])

    public var int: Int? {
        switch self {
        case .int(let v): return Int(v)
        case .uint(let v): return Int(v)
        default: return nil
        }
    }
    public var double: Double? {
        switch self {
        case .float(let v): return v
        case .int(let v): return Double(v)
        case .uint(let v): return Double(v)
        default: return nil
        }
    }
    public var string: String? { if case .string(let s) = self { return s } else { return nil } }
    public var array: [GGUFValue]? { if case .array(let a) = self { return a } else { return nil } }
}

public struct GGUFTensorInfo: Sendable {
    public let name: String
    /// ne[0] first (ne[0] = row length, contiguous).
    public let dims: [Int]
    public let typeRaw: UInt32
    public let offset: Int   // from the start of the data section
    public var count: Int { dims.reduce(1, *) }
    public var rowLength: Int { dims.first ?? 0 }
    public var rows: Int { count / max(rowLength, 1) }
}

/// Read-only memory map of a file (POSIX mmap; pages come from disk on demand).
public final class MappedFile: @unchecked Sendable {
    public let base: UnsafeRawPointer
    public let size: Int

    public init(path: String) throws {
        let fd = open(path, O_RDONLY)
        guard fd >= 0 else { throw GGUFError.open(path) }
        defer { close(fd) }
        var st = stat()
        guard fstat(fd, &st) == 0, st.st_size > 0 else { throw GGUFError.open(path) }
        let n = Int(st.st_size)
        guard let p = mmap(nil, n, PROT_READ, MAP_PRIVATE, fd, 0), p != MAP_FAILED else { throw GGUFError.open(path) }
        base = UnsafeRawPointer(p)
        size = n
    }
    deinit { munmap(UnsafeMutableRawPointer(mutating: base), size) }
}

public final class GGUFFile: @unchecked Sendable {
    public let file: MappedFile
    public let version: UInt32
    public private(set) var metadata: [String: GGUFValue] = [:]
    public private(set) var tensors: [String: GGUFTensorInfo] = [:]
    public private(set) var tensorOrder: [String] = []
    public let alignment: Int
    public let dataOffset: Int

    public convenience init(path: String) throws {
        try self.init(file: MappedFile(path: path))
    }

    public init(file: MappedFile) throws {
        self.file = file
        var r = Reader(base: file.base, size: file.size)
        guard try r.u32() == 0x4655_4747 else { throw GGUFError.badMagic }  // "GGUF" little-endian
        version = try r.u32()
        guard version == 2 || version == 3 else { throw GGUFError.unsupportedVersion(version) }
        let nTensors = Int(try r.u64())
        let nKV = Int(try r.u64())
        var meta: [String: GGUFValue] = [:]
        for _ in 0..<nKV {
            let key = try r.string()
            let type = try r.u32()
            meta[key] = try r.value(type)
        }
        var infos: [String: GGUFTensorInfo] = [:]
        var order: [String] = []
        for _ in 0..<nTensors {
            let name = try r.string()
            let nd = Int(try r.u32())
            guard nd >= 1 && nd <= 4 else { throw GGUFError.shape("\(name) has \(nd) dims") }
            var dims: [Int] = []
            for _ in 0..<nd { dims.append(Int(try r.u64())) }
            let t = try r.u32()
            let off = Int(try r.u64())
            infos[name] = GGUFTensorInfo(name: name, dims: dims, typeRaw: t, offset: off)
            order.append(name)
        }
        let align = meta["general.alignment"]?.int ?? 32
        alignment = align
        dataOffset = (r.pos + align - 1) / align * align
        metadata = meta
        tensors = infos
        tensorOrder = order
    }

    public func tensor(_ name: String) throws -> GGUFTensor {
        guard let info = tensors[name] else { throw GGUFError.missingTensor(name) }
        guard let type = GGMLType(rawValue: info.typeRaw) else { throw GGUFError.unsupportedTensorType(name, info.typeRaw) }
        guard info.rowLength % type.block.n == 0 else { throw GGUFError.shape("\(name) row \(info.rowLength) not a multiple of \(type.block.n)") }
        let bytes = type.rowBytes(info.rowLength) * info.rows
        let start = dataOffset + info.offset
        guard start >= 0, start + bytes <= file.size else { throw GGUFError.truncated(name) }
        return GGUFTensor(info: info, type: type, data: file.base + start, owner: file)
    }

    public func int(_ key: String) throws -> Int {
        guard let v = metadata[key]?.int else { throw GGUFError.missingKey(key) }
        return v
    }
    public func double(_ key: String) -> Double? { metadata[key]?.double }
    public func string(_ key: String) -> String? { metadata[key]?.string }

    struct Reader {
        let base: UnsafeRawPointer
        let size: Int
        var pos = 0
        mutating func need(_ n: Int) throws {
            guard n >= 0, pos + n <= size else { throw GGUFError.truncated("at byte \(pos)") }
        }
        mutating func u8() throws -> UInt8 { try need(1); defer { pos += 1 }; return base.load(fromByteOffset: pos, as: UInt8.self) }
        mutating func u16() throws -> UInt16 { try need(2); defer { pos += 2 }; return base.loadUnaligned(fromByteOffset: pos, as: UInt16.self) }
        mutating func u32() throws -> UInt32 { try need(4); defer { pos += 4 }; return base.loadUnaligned(fromByteOffset: pos, as: UInt32.self) }
        mutating func u64() throws -> UInt64 { try need(8); defer { pos += 8 }; return base.loadUnaligned(fromByteOffset: pos, as: UInt64.self) }
        mutating func string() throws -> String {
            let n = Int(try u64())
            try need(n)
            let s = String(decoding: UnsafeRawBufferPointer(start: base + pos, count: n), as: UTF8.self)
            pos += n
            return s
        }
        mutating func value(_ type: UInt32) throws -> GGUFValue {
            switch type {
            case 0: return .uint(UInt64(try u8()))
            case 1: return .int(Int64(Int8(bitPattern: try u8())))
            case 2: return .uint(UInt64(try u16()))
            case 3: return .int(Int64(Int16(bitPattern: try u16())))
            case 4: return .uint(UInt64(try u32()))
            case 5: return .int(Int64(Int32(bitPattern: try u32())))
            case 6: return .float(Double(Float(bitPattern: try u32())))
            case 7: return .bool(try u8() != 0)
            case 8: return .string(try string())
            case 9:
                let t = try u32()
                let n = Int(try u64())
                guard n <= size else { throw GGUFError.truncated("array of \(n)") }
                var out: [GGUFValue] = []
                out.reserveCapacity(n)
                for _ in 0..<n { out.append(try value(t)) }
                return .array(out)
            case 10: return .uint(try u64())
            case 11: return .int(Int64(bitPattern: try u64()))
            case 12: return .float(Double(bitPattern: try u64()))
            default: throw GGUFError.badValueType(type)
            }
        }
    }
}

/// A view of one tensor's bytes inside the mapped file.
public struct GGUFTensor: @unchecked Sendable {
    public let info: GGUFTensorInfo
    public let type: GGMLType
    public let data: UnsafeRawPointer
    let owner: MappedFile   // keeps the mapping alive

    public var rowLength: Int { info.rowLength }
    public var rows: Int { info.rows }

    /// Dequantise row `r` into `out` (count >= rowLength).
    public func row(_ r: Int, into out: UnsafeMutablePointer<Float>) {
        let rb = type.rowBytes(rowLength)
        GGMLDequant.row(type, data + r * rb, rowLength, out)
    }
    public func row(_ r: Int) -> [Float] {
        var out = [Float](repeating: 0, count: rowLength)
        out.withUnsafeMutableBufferPointer { row(r, into: $0.baseAddress!) }
        return out
    }
    /// The whole tensor as Float (small tensors only: norms, biases, tests).
    public func floats() -> [Float] {
        var out = [Float](repeating: 0, count: info.count)
        out.withUnsafeMutableBufferPointer { b in
            for r in 0..<rows { row(r, into: b.baseAddress! + r * rowLength) }
        }
        return out
    }
}

public enum GGMLDequant {
    @inline(__always) static func f16(_ p: UnsafeRawPointer, _ off: Int) -> Float {
        halfToFloat(p.loadUnaligned(fromByteOffset: off, as: UInt16.self))
    }

    /// IEEE 754 binary16 -> Float (handles subnormals, inf, NaN). Portable (no Float16 on x86 Linux).
    public static func halfToFloat(_ h: UInt16) -> Float {
        let sign = UInt32(h & 0x8000) << 16
        let exp = Int((h >> 10) & 0x1F)
        let man = UInt32(h & 0x3FF)
        if exp == 0 {
            if man == 0 { return Float(bitPattern: sign) }
            let v = Float(man) * Float(sign: .plus, exponent: -24, significand: 1)
            return sign != 0 ? -v : v
        }
        if exp == 31 { return Float(bitPattern: sign | 0x7F80_0000 | (man << 13)) }
        return Float(bitPattern: sign | UInt32(exp - 15 + 127) << 23 | (man << 13))
    }

    /// Float -> binary16, round-to-nearest-even (used by tests and fixture writers).
    public static func floatToHalf(_ f: Float) -> UInt16 {
        let b = f.bitPattern
        let sign = UInt16((b >> 16) & 0x8000)
        let exp = Int((b >> 23) & 0xFF) - 127 + 15
        var man = b & 0x7F_FFFF
        if (b >> 23) & 0xFF == 0xFF { return sign | 0x7C00 | (man != 0 ? 0x200 : 0) }
        if exp >= 31 { return sign | 0x7C00 }
        if exp <= 0 {
            if exp < -10 { return sign }
            man |= 0x80_0000
            let shift = UInt32(14 - exp)
            var h = man >> shift
            let rem = man & ((1 << shift) - 1)
            let half = UInt32(1) << (shift - 1)
            if rem > half || (rem == half && (h & 1) == 1) { h += 1 }
            return sign | UInt16(h)
        }
        var h = UInt32(exp) << 10 | (man >> 13)
        let rem = man & 0x1FFF
        if rem > 0x1000 || (rem == 0x1000 && (h & 1) == 1) { h += 1 }
        return sign | UInt16(truncatingIfNeeded: h)
    }

    @inline(__always) static func scaleMinK4(_ j: Int, _ q: UnsafeRawPointer) -> (Float, Float) {
        func b(_ i: Int) -> UInt8 { q.load(fromByteOffset: i, as: UInt8.self) }
        if j < 4 { return (Float(b(j) & 63), Float(b(j + 4) & 63)) }
        let d = (b(j + 4) & 0xF) | ((b(j - 4) >> 6) << 4)
        let m = (b(j + 4) >> 4) | ((b(j) >> 6) << 4)
        return (Float(d), Float(m))
    }

    public static func row(_ type: GGMLType, _ src: UnsafeRawPointer, _ n: Int, _ y: UnsafeMutablePointer<Float>) {
        switch type {
        case .f32:
            for i in 0..<n { y[i] = src.loadUnaligned(fromByteOffset: 4 * i, as: Float.self) }
        case .f16:
            for i in 0..<n { y[i] = f16(src, 2 * i) }
        case .q8_0:
            for b in 0..<(n / 32) {
                let blk = src + b * 34
                let d = f16(blk, 0)
                let q = (blk + 2).assumingMemoryBound(to: Int8.self)
                for j in 0..<32 { y[b * 32 + j] = d * Float(q[j]) }
            }
        case .q5_0:
            for b in 0..<(n / 32) {
                let blk = src + b * 22
                let d = f16(blk, 0)
                let qh = blk.loadUnaligned(fromByteOffset: 2, as: UInt32.self)
                let qs = (blk + 6).assumingMemoryBound(to: UInt8.self)
                for j in 0..<16 {
                    let xh0 = UInt8(truncatingIfNeeded: ((qh >> UInt32(j)) << 4) & 0x10)
                    let xh1 = UInt8(truncatingIfNeeded: (qh >> UInt32(j + 12)) & 0x10)
                    let x0 = Int32((qs[j] & 0x0F) | xh0) - 16
                    let x1 = Int32((qs[j] >> 4) | xh1) - 16
                    y[b * 32 + j] = Float(x0) * d
                    y[b * 32 + j + 16] = Float(x1) * d
                }
            }
        case .q4_K:
            for b in 0..<(n / 256) {
                let blk = src + b * 144
                let d = f16(blk, 0)
                let dmin = f16(blk, 2)
                let scales = blk + 4
                var q = (blk + 16).assumingMemoryBound(to: UInt8.self)
                var out = y + b * 256
                var s = 0
                for _ in 0..<4 {
                    let (sc1, m1) = scaleMinK4(s, scales)
                    let (sc2, m2) = scaleMinK4(s + 1, scales)
                    let d1 = d * sc1, mm1 = dmin * m1
                    let d2 = d * sc2, mm2 = dmin * m2
                    for l in 0..<32 { out[l] = d1 * Float(q[l] & 0xF) - mm1 }
                    for l in 0..<32 { out[32 + l] = d2 * Float(q[l] >> 4) - mm2 }
                    out += 64; q += 32; s += 2
                }
            }
        case .q6_K:
            for b in 0..<(n / 256) {
                let blk = src + b * 210
                var ql = blk.assumingMemoryBound(to: UInt8.self)
                var qh = (blk + 128).assumingMemoryBound(to: UInt8.self)
                var sc = (blk + 192).assumingMemoryBound(to: Int8.self)
                let d = f16(blk, 208)
                var out = y + b * 256
                for _ in 0..<2 {
                    for l in 0..<32 {
                        let i = l / 16
                        let q1 = Int32((ql[l] & 0xF) | (((qh[l] >> 0) & 3) << 4)) - 32
                        let q2 = Int32((ql[l + 32] & 0xF) | (((qh[l] >> 2) & 3) << 4)) - 32
                        let q3 = Int32((ql[l] >> 4) | (((qh[l] >> 4) & 3) << 4)) - 32
                        let q4 = Int32((ql[l + 32] >> 4) | (((qh[l] >> 6) & 3) << 4)) - 32
                        out[l] = d * Float(sc[i]) * Float(q1)
                        out[l + 32] = d * Float(sc[i + 2]) * Float(q2)
                        out[l + 64] = d * Float(sc[i + 4]) * Float(q3)
                        out[l + 96] = d * Float(sc[i + 6]) * Float(q4)
                    }
                    out += 128; ql += 64; qh += 32; sc += 8
                }
            }
        }
    }
}
