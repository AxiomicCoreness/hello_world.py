package com.fruitfly.brain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * SovereignAutomaton.step must deliver each presynaptic neuron's connectome
 * currents to the postsynaptic targets, not back into the presynaptic neuron.
 */
class SovereignAutomatonPropagationTest {

    private static final double DT = 1e-3;   // 1 ms, equal to the edge delay
    private static final double DRIVE = 0.5;
    private static final int STEPS = 10;

    /** Two neurons, one synapse 0 -> 1 (weight 10, delay 1 ms), via the CSR constructor. */
    private static Connectome singleEdge() {
        return new Connectome(2,
                new int[] {0, 1, 1},
                new int[] {1},
                new double[] {10.0},
                new double[] {1.0});
    }

    /** Same two neurons, no synapses. */
    private static Connectome noEdges() {
        return new Connectome(2,
                new int[] {0, 0, 0},
                new int[] {},
                new double[] {},
                new double[] {});
    }

    private static SovereignAutomaton run(Connectome c) {
        SovereignAutomaton a = new SovereignAutomaton(c, 2);
        for (int s = 0; s < STEPS; s++) {
            a.step(DT, DRIVE);
        }
        return a;
    }

    @Test
    void currentReachesPostsynapticNeuronOnly() {
        SovereignAutomaton wired = run(singleEdge());
        SovereignAutomaton bare = run(noEdges());

        double v0Wired = wired.swarm().get(0).v();
        double v0Bare = bare.swarm().get(0).v();
        double v1Wired = wired.swarm().get(1).v();
        double v1Bare = bare.swarm().get(1).v();

        // Presynaptic neuron 0 has no incoming edge, so it must evolve exactly
        // as it does with no connectome edges at all.
        assertEquals(v0Bare, v0Wired, 0.0, "neuron 0 must not receive its own outgoing current");
        // Postsynaptic neuron 1 receives 0 -> 1, so its voltage must differ.
        assertNotEquals(v1Bare, v1Wired, "neuron 1 must receive the 0 -> 1 current");
        assertTrue(Math.abs(v1Wired - v1Bare) > 1e-6,
                "neuron 1 voltage difference too small: " + (v1Wired - v1Bare));
        assertEquals(wired.time(), bare.time(), 0.0);
        assertEquals(wired.state(), bare.state());
    }

    @Test
    void respondFormatUnchanged() {
        SovereignAutomaton a = new SovereignAutomaton(noEdges(), 2);
        assertEquals("", a.respond("", 0.5, 0.25));
        assertEquals("", a.respond(null, 0.5, 0.25));
        String reply = a.respond("hi", 0.5, 0.25);
        assertEquals(String.format("phase=%s q=%.4f p=%.4f t=%.6f",
                SovereigntyState.RESONANCE, 0.5, 0.25, 1e-4), reply);
        assertTrue(reply.matches("phase=[A-Z_]+ q=\\S+ p=\\S+ t=\\S+"), reply);
        assertTrue(a.gate());
    }
    // ---- per-substep delivery: a delay of d ms lands at substep ceil(d / dt) ----

    private static final double SUB_MS = LIFRK4.BRAIN_TICK_MS / LIFRK4.SUBSTEPS;

    private static Connectome edge(double w, double delayMs) {
        return new Connectome(2,
                new int[] {0, 1, 1},
                new int[] {1},
                new double[] {w},
                new double[] {delayMs});
    }

    /** Closed form of LIFRK4 from rest with g = g0 at t = 0 (ms). */
    private static double exactFromRest(double g0, double t) {
        double a = g0 * LIFRK4.TAU_G / (LIFRK4.TAU_G - LIFRK4.TAU_V);
        return LIFRK4.V_REST - a * Math.exp(-t / LIFRK4.TAU_V) + a * Math.exp(-t / LIFRK4.TAU_G);
    }

    @Test
    void delayLandsAtCeilSubstep() {
        double w = 0.1;
        double q = w * LIFRK4.V_REST; // neuron 0 sits at rest, so it sends w * V_REST
        double[][] cases = {{0.25, 1}, {1.0, 1}, {2.5, 3}, {3.0, 3}, {17.2, 18}};
        for (double[] c : cases) {
            assertEquals((int) c[1], SovereignAutomaton.delaySubsteps(c[0]), "ceil for d=" + c[0]);
            SovereignAutomaton a = new SovereignAutomaton(edge(w, c[0]), 2);
            a.step(DT, 0.0);
            double t = LIFRK4.BRAIN_TICK_MS - c[1] * SUB_MS;
            assertEquals(exactFromRest(q, t), a.swarm().get(1).v(), 1e-5, "delay " + c[0] + " ms");
            assertEquals(LIFRK4.V_REST, a.swarm().get(0).v(), 0.0);
        }
    }

    @Test
    void delayLongerThanTickCarriesIntoNextTick() {
        double w = 0.1;
        double q = w * LIFRK4.V_REST;
        SovereignAutomaton a = new SovereignAutomaton(edge(w, 60.0), 2); // substep 60 = tick 1, substep 10
        a.step(DT, 0.0);
        assertEquals(LIFRK4.V_REST, a.swarm().get(1).v(), 0.0, "nothing arrives in the first tick");
        a.step(DT, 0.0);
        assertEquals(exactFromRest(q, LIFRK4.BRAIN_TICK_MS - 10 * SUB_MS), a.swarm().get(1).v(), 1e-5);
    }

    /** Drive lands at substep 0; per-tick charge into g is drive + sum(w * vPre), as before. */
    @Test
    void driveAtSubstepZeroAndChargeConserved() {
        SovereignAutomaton a = new SovereignAutomaton(noEdges(), 2);
        a.step(DT, 20.0);
        assertEquals(exactFromRest(20.0, LIFRK4.BRAIN_TICK_MS), a.swarm().get(0).v(), 1e-5);

        double w = 0.1;
        double drive = 5.0;
        SovereignAutomaton b = new SovereignAutomaton(edge(w, 2.5), 2);
        b.step(DT, drive);
        LIFRK4 ref = new LIFRK4();
        double[] in = new double[LIFRK4.SUBSTEPS];
        in[0] = drive;
        in[3] = w * LIFRK4.V_REST;
        ref.stepTick(in);
        assertEquals(ref.v(), b.swarm().get(1).v(), 0.0);
        assertEquals(ref.g(), b.swarm().get(1).g(), 0.0);
        assertEquals(drive + w * LIFRK4.V_REST, in[0] + in[3], 0.0);
    }
}
