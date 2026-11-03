// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT
//
// DarkStateInvariant — spectral check on a square transition/update matrix A.
//
// Passes only when
//   * λ₁ = 1 is an eigenvalue with algebraic multiplicity exactly 1 (simple), and
//   * every other eigenvalue satisfies |λ| < 1, i.e. the spectral gap 1 − |λ₂| > 0,
// which makes the fixed point (attractor) of x ← A·x unique.
//
// With learning rate η = 1 each update fully replaces the tensor (x_{k+1} = A·x_k, nothing of
// x_k is blended back in), so no damping term helps or hurts: the gap alone governs
// convergence, and the distance to the attractor shrinks like |λ₂|^k.
//
// Failure modes it reports:
//   * λ₂ = 1 (multiplicity ≥ 2) — two or more absorbing classes, no unique attractor;
//   * an eigenvalue on the unit circle other than 1 (e.g. a complex pair e^{±iθ}, or −1) —
//     a resonator that oscillates forever instead of converging;
//   * |λ| > 1 — divergence; or 1 not an eigenvalue at all.
//
// Eigenvalues come from the characteristic polynomial (Faddeev–LeVerrier) and Durand–Kerner
// root finding in pure Foundation; intended for the small matrices used here (n ≤ 16).
import Foundation

public struct DarkStateInvariant {
    public struct Complex: Equatable {
        public var re: Double
        public var im: Double
        public init(_ re: Double, _ im: Double = 0) { self.re = re; self.im = im }
        public var magnitude: Double { (re * re + im * im).squareRoot() }
        static func + (a: Complex, b: Complex) -> Complex { Complex(a.re + b.re, a.im + b.im) }
        static func - (a: Complex, b: Complex) -> Complex { Complex(a.re - b.re, a.im - b.im) }
        static func * (a: Complex, b: Complex) -> Complex {
            Complex(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re)
        }
        static func / (a: Complex, b: Complex) -> Complex {
            let d = b.re * b.re + b.im * b.im
            return Complex((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d)
        }
    }

    public enum Verdict: Equatable {
        case uniqueAttractor(gap: Double)
        case notSquare
        case noUnitEigenvalue
        case multipleAbsorbingClasses(multiplicity: Int)
        case resonator(Complex)
        case divergent(Complex)
    }

    public struct Report: Equatable {
        public let eigenvalues: [Complex]
        public let lambda2Magnitude: Double
        public let verdict: Verdict
        public var holds: Bool { if case .uniqueAttractor = verdict { return true }; return false }
    }

    /// η = 1: the update fully replaces the tensor, so only the spectral gap matters.
    public static let learningRate: Double = 1

    public static func check(_ a: [[Double]], tolerance: Double = 1e-6) -> Report {
        let n = a.count
        guard n > 0, a.allSatisfy({ $0.count == n }) else {
            return Report(eigenvalues: [], lambda2Magnitude: .nan, verdict: .notSquare)
        }
        let eig = eigenvalues(a)
        let isOne: (Complex) -> Bool = { ($0 - Complex(1)).magnitude < tolerance }
        let ones = eig.filter(isOne).count
        let rest = eig.filter { !isOne($0) }.sorted { $0.magnitude > $1.magnitude }
        let l2 = ones >= 2 ? 1.0 : (rest.first?.magnitude ?? 0)
        let verdict: Verdict
        if ones == 0 {
            verdict = .noUnitEigenvalue
        } else if ones > 1 {
            verdict = .multipleAbsorbingClasses(multiplicity: ones)
        } else if let top = rest.first, top.magnitude > 1 + tolerance {
            verdict = .divergent(top)
        } else if let top = rest.first, top.magnitude >= 1 - tolerance {
            verdict = .resonator(top)
        } else {
            verdict = .uniqueAttractor(gap: 1 - l2)
        }
        return Report(eigenvalues: eig, lambda2Magnitude: l2, verdict: verdict)
    }

    /// Characteristic polynomial coefficients c[0..n] of det(λI − A), c[0] = 1 (Faddeev–LeVerrier).
    static func characteristicPolynomial(_ a: [[Double]]) -> [Double] {
        let n = a.count
        var c = [Double](repeating: 0, count: n + 1)
        c[0] = 1
        var m = [[Double]](repeating: [Double](repeating: 0, count: n), count: n)  // M_0 = 0
        for k in 1...n {
            // M_k = A·M_{k-1} + c_{k-1}·I
            var next = [[Double]](repeating: [Double](repeating: 0, count: n), count: n)
            for i in 0..<n {
                for j in 0..<n {
                    var s = 0.0
                    for t in 0..<n { s += a[i][t] * m[t][j] }
                    next[i][j] = s + (i == j ? c[k - 1] : 0)
                }
            }
            m = next
            var tr = 0.0
            for i in 0..<n { for t in 0..<n { tr += a[i][t] * m[t][i] } }
            c[k] = -tr / Double(k)
        }
        return c
    }

    /// All n eigenvalues via Durand–Kerner on the monic characteristic polynomial.
    public static func eigenvalues(_ a: [[Double]]) -> [Complex] {
        let c = characteristicPolynomial(a)
        let n = c.count - 1
        if n == 1 { return [Complex(-c[1])] }
        func p(_ z: Complex) -> Complex { c.reduce(Complex(0)) { $0 * z + Complex($1) } }
        let seed = Complex(0.4, 0.9)
        var z = (0..<n).map { k -> Complex in
            var w = Complex(1)
            for _ in 0..<k { w = w * seed }
            return w
        }
        for _ in 0..<2000 {
            var delta = 0.0
            for i in 0..<n {
                var den = Complex(1)
                for j in 0..<n where j != i { den = den * (z[i] - z[j]) }
                if den.magnitude == 0 { den = Complex(1e-12) }
                let step = p(z[i]) / den
                z[i] = z[i] - step
                delta = max(delta, step.magnitude)
            }
            if delta < 1e-14 { break }
        }
        return z.map { Complex(abs($0.re) < 1e-12 ? 0 : $0.re, abs($0.im) < 1e-9 ? 0 : $0.im) }
    }
}
