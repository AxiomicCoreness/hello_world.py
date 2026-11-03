// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import PocketCore

final class DarkStateInvariantTests: XCTestCase {
    func testUniqueAttractorPasses() {
        // Column-stochastic, irreducible, aperiodic: eigenvalues 1 and 0.7.
        let a: [[Double]] = [[0.9, 0.2], [0.1, 0.8]]
        let r = DarkStateInvariant.check(a)
        XCTAssertTrue(r.holds, "\(r.verdict)")
        XCTAssertEqual(r.lambda2Magnitude, 0.7, accuracy: 1e-6)
        if case .uniqueAttractor(let gap) = r.verdict {
            XCTAssertEqual(gap, 0.3, accuracy: 1e-6)
            XCTAssertGreaterThan(gap, 0)
        } else { XCTFail("expected unique attractor, got \(r.verdict)") }
    }

    func testThreeStateUniqueAttractorPasses() {
        let a: [[Double]] = [[0.5, 0.25, 0.25], [0.25, 0.5, 0.25], [0.25, 0.25, 0.5]]
        let r = DarkStateInvariant.check(a)   // eigenvalues 1, 0.25, 0.25
        XCTAssertTrue(r.holds, "\(r.verdict)")
        XCTAssertEqual(r.lambda2Magnitude, 0.25, accuracy: 1e-5)
    }

    func testTwoAbsorbingClassesFails() {
        // λ₂ = 1: two absorbing states, no unique attractor.
        let a: [[Double]] = [[1, 0, 0.5], [0, 1, 0.5], [0, 0, 0]]
        let r = DarkStateInvariant.check(a)
        XCTAssertFalse(r.holds)
        XCTAssertEqual(r.verdict, .multipleAbsorbingClasses(multiplicity: 2))
        XCTAssertEqual(r.lambda2Magnitude, 1)
    }

    func testComplexPairOnUnitCircleIsResonator() {
        // 3-cycle permutation: eigenvalues 1, e^{±2πi/3} — oscillates forever.
        let a: [[Double]] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
        let r = DarkStateInvariant.check(a)
        XCTAssertFalse(r.holds)
        guard case .resonator(let z) = r.verdict else { return XCTFail("got \(r.verdict)") }
        XCTAssertEqual(z.magnitude, 1, accuracy: 1e-6)
        XCTAssertNotEqual(z.im, 0)
    }

    func testNonSquareRejected() {
        XCTAssertEqual(DarkStateInvariant.check([[1, 0]]).verdict, .notSquare)
    }

    func testLearningRateIsOne() {
        XCTAssertEqual(DarkStateInvariant.learningRate, 1)
    }
}
