package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Behaviour of the LIFRK4 port (src/main/java/com/fruitfly/brain/LIFRK4.java). */
class LifNeuronTest {

    @Test
    void constantsMatchLifRk4() {
        assertEquals(-52.0, LifNeuron.V_REST);
        assertEquals(-45.0, LifNeuron.V_THRESH);
        assertEquals(-52.0, LifNeuron.V_RESET);
        assertEquals(20.0, LifNeuron.TAU_V);
        assertEquals(5.0, LifNeuron.TAU_G);
        assertEquals(2.2, LifNeuron.REFRAC);
        assertEquals(50.0, LifNeuron.BRAIN_TICK_MS);
        assertEquals(50, LifNeuron.SUBSTEPS);
        assertEquals(1.0, LifNeuron.DT_MS);
    }

    @Test
    void staysAtRestWithNoInput() {
        LifNeuron n = new LifNeuron();
        assertEquals(0, n.stepTick(new double[LifNeuron.SUBSTEPS]));
        assertEquals(LifNeuron.V_REST, n.v(), 1e-12);
        assertEquals(0.0, n.g(), 1e-12);
    }

    @Test
    void subthresholdPulseDoesNotSpikeAndDecays() {
        LifNeuron n = new LifNeuron();
        double[] in = new double[LifNeuron.SUBSTEPS];
        in[0] = 40.0; // peak ~ 0.1575 * 40 = 6.3 mV < 7 mV gap
        assertEquals(0, n.stepTick(in));
        assertTrue(n.v() > LifNeuron.V_REST);
        assertTrue(n.v() < LifNeuron.V_THRESH);
    }

    @Test
    void suprathresholdPulseSpikesInsideTheTickAndGoesRefractory() {
        LifNeuron n = new LifNeuron();
        int spikeAt = -1;
        for (int s = 0; s < LifNeuron.SUBSTEPS; s++) {
            if (n.substep(s == 0 ? 60.0 : 0.0, LifNeuron.DT_MS)) {
                spikeAt = s;
                assertEquals(LifNeuron.V_RESET, n.v());
                assertEquals(LifNeuron.REFRAC, n.refractoryRemaining());
                break;
            }
        }
        // the per-substep check catches the crossing a few ms in, not at the tick end
        assertEquals(3, spikeAt);
    }

    @Test
    void refractoryClampsVoltageAtReset() {
        LifNeuron n = new LifNeuron();
        assertTrue(n.substep(500.0, LifNeuron.DT_MS)); // huge pulse: spike on substep 0
        assertFalse(n.substep(0.0, LifNeuron.DT_MS)); // 2.2 -> 1.2 ms left
        assertEquals(LifNeuron.V_RESET, n.v());
        assertFalse(n.substep(0.0, LifNeuron.DT_MS)); // 1.2 -> 0.2 ms left
        assertEquals(LifNeuron.V_RESET, n.v());
    }

    @Test
    void stepTickRejectsWrongLength() {
        assertThrows(IllegalArgumentException.class, () -> new LifNeuron().stepTick(new double[3]));
        assertThrows(IllegalArgumentException.class, () -> new LifNeuron().stepTick(null));
    }
}
