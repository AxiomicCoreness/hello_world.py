package com.fruitfly.brain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

import org.junit.jupiter.api.Test;

/**
 * LIFRK4 against the closed-form solution of its own ODE pair
 * (all times in ms, the units of TAU_V, TAU_G, REFRAC and BRAIN_TICK_MS):
 *
 *   dv/dt = (V_REST - v + g) / TAU_V      (R*I folded into g, in mV)
 *   dg/dt = -g / TAU_G
 *
 * With u = v - V_REST and A = g0 * TAU_G / (TAU_G - TAU_V):
 *
 *   g(t) = g0 e^{-t/TAU_G}
 *   u(t) = (u0 - A) e^{-t/TAU_V} + A e^{-t/TAU_G}
 *
 * As TAU_G -> infinity (g held constant = I_eff) this reduces to
 * u0 e^{-a t} + (I_eff / (a TAU_V)) (1 - e^{-a t}) with a = 1/TAU_V,
 * i.e. V_n e^{-a dt} + (I/a)(1 - e^{-a dt}) with I = g/TAU_V.
 */
class LIFRK4Test {

    private static final double DT = LIFRK4.BRAIN_TICK_MS / LIFRK4.SUBSTEPS; // 1 ms

    private static double exactV(double v0, double g0, double t) {
        double a = g0 * LIFRK4.TAU_G / (LIFRK4.TAU_G - LIFRK4.TAU_V);
        double u0 = v0 - LIFRK4.V_REST;
        return LIFRK4.V_REST
                + (u0 - a) * Math.exp(-t / LIFRK4.TAU_V)
                + a * Math.exp(-t / LIFRK4.TAU_G);
    }

    private static double exactG(double g0, double t) {
        return g0 * Math.exp(-t / LIFRK4.TAU_G);
    }

    /** Leading RK4 local truncation error of g' = -g/TAU_G over one step dt. */
    private static double localErrorBound(double g0, double dt) {
        return Math.abs(g0) * Math.pow(dt / LIFRK4.TAU_G, 5) / 120.0;
    }

    private static void rk4(LIFRK4 n, double dt) throws Exception {
        Method m = LIFRK4.class.getDeclaredMethod("stepRK4", double.class);
        m.setAccessible(true);
        m.invoke(n, dt);
    }

    private static void setRefractory(LIFRK4 n, double ms) throws Exception {
        Field f = LIFRK4.class.getDeclaredField("refractoryRemaining");
        f.setAccessible(true);
        f.setDouble(n, ms);
    }

    /** A neuron with v = V_REST and g = g0 (stepTick adds gDelta after its substeps). */
    private static LIFRK4 primed(double g0) {
        LIFRK4 n = new LIFRK4();
        n.stepTick(g0);
        assertEquals(LIFRK4.V_REST, n.v(), 0.0);
        assertEquals(g0, n.g(), 0.0);
        return n;
    }

    @Test
    void oneSubstepMatchesExactSolution() throws Exception {
        LIFRK4 n = primed(20.0);
        // move off V_REST first so u0 != 0 is exercised too
        rk4(n, 3.0);
        double v0 = n.v();
        double g0 = n.g();
        assertTrue(v0 - LIFRK4.V_REST > 0.5, "setup: u0 = " + (v0 - LIFRK4.V_REST));

        rk4(n, DT);
        // RK4 local error for e^{-x}: |g0| x^5 / 120 with x = DT/TAU_G (2.4e-5 here)
        double tol = 1.5 * localErrorBound(g0, DT);
        assertEquals(exactV(v0, g0, DT), n.v(), tol, "v after one RK4 substep");
        assertEquals(exactG(g0, DT), n.g(), tol, "g after one RK4 substep");
    }

    @Test
    void globalErrorIsFourthOrder() throws Exception {
        double g0 = 20.0;
        double horizon = 8.0;
        double[] dts = {2.0, 1.0, 0.5, 0.25};
        double[] err = new double[dts.length];
        for (int k = 0; k < dts.length; k++) {
            LIFRK4 n = primed(g0);
            int steps = (int) Math.round(horizon / dts[k]);
            for (int s = 0; s < steps; s++) {
                rk4(n, dts[k]);
            }
            err[k] = Math.abs(n.v() - exactV(LIFRK4.V_REST, g0, horizon));
        }
        for (int k = 1; k < dts.length; k++) {
            double ratio = err[k - 1] / err[k];
            assertTrue(ratio > 14.0 && ratio < 20.0,
                    String.format("halving dt %.3f -> %.3f: error ratio %.2f (want ~16)",
                            dts[k - 1], dts[k], ratio));
        }
    }

    @Test
    void subthresholdTickMatchesExactSolution() {
        double g0 = 20.0; // peak u = g0 * 0.1575 = 3.15 mV < 7 mV, never spikes
        LIFRK4 n = primed(g0);
        n.stepTick(0.0);
        assertEquals(exactV(LIFRK4.V_REST, g0, LIFRK4.BRAIN_TICK_MS), n.v(), 1e-5);
        assertEquals(exactG(g0, LIFRK4.BRAIN_TICK_MS), n.g(), 1e-5);
        assertEquals(0.0, n.refractoryRemaining(), 0.0);
    }

    @Test
    void refractoryClampsVoltageAndStillDecaysG() throws Exception {
        LIFRK4 n = primed(30.0);
        rk4(n, 4.0);
        assertTrue(n.v() > LIFRK4.V_RESET + 1.0);
        double g0 = n.g();
        setRefractory(n, LIFRK4.REFRAC);
        rk4(n, DT);
        assertEquals(LIFRK4.V_RESET, n.v(), 0.0, "v clamped while refractory");
        assertEquals(exactG(g0, DT), n.g(), 1.5 * localErrorBound(g0, DT),
                "g keeps decaying while refractory");
    }

    /**
     * g0 = 100 drives u over threshold (7 mV) between t = 1 and 2 ms and back
     * below it long before the 50 ms tick ends (exact u(50) = 2.74 mV).
     * The spike must be caught at the substep it happens, then v is held at
     * V_RESET for ceil(REFRAC / DT) = 3 substeps, then integrates again.
     */
    @Test
    void midTickCrossingSpikesAndResets() {
        double g0 = 100.0;
        assertTrue(exactV(LIFRK4.V_REST, g0, 1.0) < LIFRK4.V_THRESH);
        assertTrue(exactV(LIFRK4.V_REST, g0, 2.0) > LIFRK4.V_THRESH);
        double noSpikeEnd = exactV(LIFRK4.V_REST, g0, LIFRK4.BRAIN_TICK_MS);
        assertTrue(noSpikeEnd < LIFRK4.V_THRESH);

        LIFRK4 n = primed(g0);
        n.stepTick(0.0);

        double spikeT = 2.0;
        double releaseT = spikeT + Math.ceil(LIFRK4.REFRAC / DT) * DT; // 5 ms
        double expected = exactV(LIFRK4.V_RESET, exactG(g0, releaseT),
                LIFRK4.BRAIN_TICK_MS - releaseT);
        assertEquals(expected, n.v(), 1e-4,
                "v after a spike at 2 ms and refractory until 5 ms (no-spike value would be "
                        + noSpikeEnd + ")");
        assertEquals(exactG(g0, LIFRK4.BRAIN_TICK_MS), n.g(), 1e-5);
        assertEquals(0.0, n.refractoryRemaining(), 0.0);
    }
    // ---- per-substep input delivery: stepTick(double[]) ----

    /** Input placed at substep k leaves v at rest until t = k ms, then follows the exact solution. */
    @Test
    void perSubstepInputLandsAtItsSubstep() {
        double q = 20.0;
        for (int k : new int[] {0, 1, 3, 17, LIFRK4.SUBSTEPS - 1}) {
            LIFRK4 n = new LIFRK4();
            double[] in = new double[LIFRK4.SUBSTEPS];
            in[k] = q;
            n.stepTick(in);
            double t = LIFRK4.BRAIN_TICK_MS - k * DT;
            // a single substep (k = 49) carries one full RK4 local error, not yet damped
            double tol = Math.max(1e-5, 1.5 * localErrorBound(q, DT));
            assertEquals(exactV(LIFRK4.V_REST, q, t), n.v(), tol, "input at substep " + k);
            assertEquals(exactG(q, t), n.g(), tol, "g for input at substep " + k);
        }
    }

    /** Old scalar stepTick(Q) puts Q at the end of the tick = substep 0 of the next tick. */
    @Test
    void scalarOverloadIsSubstepZeroOfNextTick() {
        double q = 30.0;
        LIFRK4 old = new LIFRK4();
        old.stepTick(q);
        old.stepTick(0.0);

        LIFRK4 neu = new LIFRK4();
        neu.stepTick(0.0);
        double[] in = new double[LIFRK4.SUBSTEPS];
        in[0] = q;
        neu.stepTick(in);

        assertEquals(old.v(), neu.v(), 0.0);
        assertEquals(old.g(), neu.g(), 0.0);
    }

    /** Spreading a tick's input over substeps keeps its total: g gets exactly sum(q_s) decayed per substep. */
    @Test
    void perSubstepTotalChargeIsSumOfArray() throws Exception {
        LIFRK4 probe = primed(1.0);
        rk4(probe, DT);
        double r = probe.g(); // RK4 decay factor of g over one substep

        double[] in = new double[LIFRK4.SUBSTEPS];
        double total = 0.0;
        for (int s = 0; s < in.length; s++) {
            in[s] = (s % 7 == 0) ? 1.5 : ((s % 5 == 0) ? -0.4 : 0.0);
            total += in[s];
        }
        double expectedG = 0.0;
        double undecayed = 0.0;
        for (int s = 0; s < in.length; s++) {
            expectedG += in[s] * Math.pow(r, LIFRK4.SUBSTEPS - s);
            undecayed += in[s];
        }
        LIFRK4 n = new LIFRK4();
        n.stepTick(in);
        assertEquals(expectedG, n.g(), 1e-12);
        assertEquals(total, undecayed, 0.0);
    }

    @Test
    void perSubstepArrayMustHaveSubstepsLength() {
        LIFRK4 n = new LIFRK4();
        assertThrows(IllegalArgumentException.class, () -> n.stepTick(new double[LIFRK4.SUBSTEPS - 1]));
        assertThrows(IllegalArgumentException.class, () -> n.stepTick((double[]) null));
    }
}
