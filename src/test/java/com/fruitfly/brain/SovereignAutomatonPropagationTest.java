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
}
