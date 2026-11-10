// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.brain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * Seed polynomial of {@link WarriorQuadratic}: x² − x − 1 = 0.
 * Tolerances are the class's own 1e-12 gate. Nothing here loosens verify().
 */
class WarriorQuadraticTest {

    private static final double TOL = 1e-12;

    @Test
    void coefficientsAreTheSeedPolynomial() {
        assertEquals(1.0, WarriorQuadratic.A, 0.0);
        assertEquals(-1.0, WarriorQuadratic.B, 0.0);
        assertEquals(-1.0, WarriorQuadratic.C, 0.0);
        assertEquals(5.0, WarriorQuadratic.DISCRIMINANT, 0.0);
    }

    @Test
    void positiveRootIsPhi() {
        double phi = WarriorQuadratic.positiveRoot();
        assertEquals(SovereignConstants.PHI, phi, TOL);
        assertEquals(0.0, WarriorQuadratic.evaluate(phi), TOL);
        assertTrue(Math.abs(phi * phi - phi - 1.0) < TOL);
    }

    @Test
    void negativeRootIsMinusPhiInverse() {
        double phi = WarriorQuadratic.positiveRoot();
        double psi = WarriorQuadratic.negativeRoot();
        assertEquals(-1.0 / phi, psi, TOL);
        assertEquals(phi - 1.0, -psi, TOL);
        assertEquals(0.0, WarriorQuadratic.evaluate(psi), TOL);
    }

    @Test
    void vietaSumProductAndVertex() {
        assertEquals(1.0, WarriorQuadratic.positiveRoot() + WarriorQuadratic.negativeRoot(), TOL);
        assertEquals(-1.0, WarriorQuadratic.positiveRoot() * WarriorQuadratic.negativeRoot(), TOL);
        assertEquals(0.5, WarriorQuadratic.vertexX(), 0.0);
        assertTrue(WarriorQuadratic.sumResidual() < TOL);
        assertTrue(WarriorQuadratic.productResidual() < TOL);
        assertTrue(WarriorQuadratic.seedResidual() < TOL);
    }

    @Test
    void verifyHoldsAtTheClassGate() {
        assertTrue(WarriorQuadratic.verify());
        assertTrue(WarriorQuadratic.verify(TOL));
    }
}
