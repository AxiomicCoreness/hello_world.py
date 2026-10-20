package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Delivery timing follows SovereignAutomaton: ceil(delayMs / 1 ms) substeps after the sample point, carried across ticks. */
class CircuitSimTest {

    private static Circuit edge(double w, double d) {
        return ConnectomeXml.parse("<hemibrain><neuron id='A'/><neuron id='B'/>"
                + "<connection from='A' to='B' weight='" + w + "' delayMs='" + d + "'/></hemibrain>");
    }

    @Test
    void delaySubstepsMatchesSovereignAutomatonTable() {
        // Same cases as root SovereignAutomatonPropagationTest.delayLandsAtCeilSubstep, plus carry-over.
        double[][] cases = {{0.25, 1}, {1.0, 1}, {2.5, 3}, {3.0, 3}, {17.2, 18}, {50, 50}, {60, 60}};
        for (double[] c : cases) {
            assertEquals((int) c[1], CircuitSim.delaySubsteps(c[0]), "d=" + c[0]);
        }
    }

    /** Drive A at substep 0; A spikes at s0; B's g must stay 0 until substep s0 + 1 + ceil(d), then get exactly w. */
    @Test
    void spikeArrivesAtCeilSubstepAfterSamplePoint() {
        for (double d : new double[] {0.25, 1.0, 2.5, 17.2, 49.0, 60.0, 120.0}) {
            double w = 10.0;
            CircuitSim sim = new CircuitSim(edge(w, d));
            int D = CircuitSim.delaySubsteps(d);
            long s0 = -1;
            LifNeuron ref = new LifNeuron();
            for (int s = 0; s < 400; s++) {
                boolean[] sp = sim.step(new double[] {s == 0 ? LifAutoplayer.DRIVE_G : 0.0, 0.0});
                if (sp[0] && s0 < 0) {
                    s0 = s;
                }
                boolean arrives = s0 >= 0 && s == s0 + 1 + D;
                ref.substep(arrives ? w : 0.0, LifNeuron.DT_MS);
                assertEquals(ref.g(), sim.neuron(1).g(), 0.0, "d=" + d + " substep " + s);
                assertEquals(ref.v(), sim.neuron(1).v(), 0.0, "d=" + d + " substep " + s);
            }
            assertEquals(LifAutoplayer.measureLatencyMs(), s0, "A is a lone LifNeuron with the same pulse");
            assertEquals(1, sim.spikeCount(), "w=10 is sub-threshold for B");
            assertTrue(sim.neuron(1).g() != 0.0 || s0 + 1 + D >= 400);
        }
    }

    @Test
    void inhibitoryWeightIsNegativeConductance() {
        CircuitSim sim = new CircuitSim(edge(-15.0, 2.0));
        double minG = 0;
        for (int s = 0; s < 20; s++) {
            sim.step(new double[] {s == 0 ? LifAutoplayer.DRIVE_G : 0.0, 0.0});
            minG = Math.min(minG, sim.neuron(1).g());
        }
        assertTrue(minG < -10.0, "g=" + minG);
        assertTrue(sim.neuron(1).v() < LifNeuron.V_REST, "hyperpolarised");
    }

    @Test
    void lastSpikeRecorded() {
        CircuitSim sim = new CircuitSim(edge(60.0, 2.0));
        assertEquals(Long.MIN_VALUE, sim.lastSpikeSubstep(0));
        for (int s = 0; s < 30; s++) {
            sim.step(new double[] {s == 0 ? LifAutoplayer.DRIVE_G : 0.0, 0.0});
        }
        assertEquals(3, sim.lastSpikeSubstep(0));
        assertTrue(sim.lastSpikeSubstep(1) > 3);
        assertEquals(2, sim.spikeCount());
    }
}
