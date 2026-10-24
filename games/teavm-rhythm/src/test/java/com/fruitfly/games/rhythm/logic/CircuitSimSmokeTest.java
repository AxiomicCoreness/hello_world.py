package com.fruitfly.games.rhythm.logic;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.Locale;

/**
 * 1000-neuron load + step smoke test. Moved out of src/main (it had been
 * committed over irc/IrcChatCli.java in 0803c3dc) and adapted to the real
 * API: ConnectomeXml.parse(String) returns a Circuit, CircuitSim wraps it,
 * and CircuitSim.step(double[]) advances one 1 ms substep, so one 50 ms
 * tick is {@link #SUBSTEPS_PER_TICK} substeps.
 */
public class CircuitSimSmokeTest {

    private static final int NEURONS = 1000;
    private static final int SYNAPSES_PER_NEURON = 20;
    private static final int TICKS = 10; // 10 ticks * 50ms = 0.5s of simulation
    private static final int SUBSTEPS_PER_TICK = 50; // 50 x 1 ms substeps

    @Test
    public void test1000NeuronSmoke() {
        String xml = generateSyntheticCircuit(NEURONS, SYNAPSES_PER_NEURON);

        CircuitSim sim = null;
        long startLoad = System.nanoTime();
        try {
            sim = new CircuitSim(ConnectomeXml.parse(xml));
        } catch (Exception e) {
            fail("Parser threw exception: " + e.getMessage());
        }
        long endLoad = System.nanoTime();
        double loadMs = (endLoad - startLoad) / 1_000_000.0;

        assertNotNull(sim, "CircuitSim is null");
        assertEquals(NEURONS, sim.circuit().neuronCount(), "Loaded neuron count mismatch");
        assertEquals(NEURONS * SYNAPSES_PER_NEURON, sim.circuit().synapseCount(), "Loaded synapse count mismatch");

        System.out.println("Load time for " + NEURONS + " neurons: " + loadMs + " ms");
        assertTrue(loadMs < 2000, "Loading 1000 neurons took longer than 2 seconds (possible O(N^2) bottleneck)");

        // Warmup
        for (int i = 0; i < 2; i++) {
            tick(sim);
        }

        // Measured run
        long startSim = System.nanoTime();
        for (int i = 0; i < TICKS; i++) {
            tick(sim);
        }
        long endSim = System.nanoTime();
        double totalSimMs = (endSim - startSim) / 1_000_000.0;
        double msPerTick = totalSimMs / TICKS;

        System.out.printf(Locale.ROOT, "Simulation time: %.2f ms/tick (%.1f fps)%n", msPerTick, 1000.0 / msPerTick);

        // The 50ms budget check
        if (msPerTick > 50.0) {
            System.out.println("⚠️ WARNING: Exceeds 50ms frame budget!");
        } else {
            System.out.println("✅ Within 50ms frame budget.");
        }
    }

    /** One 50 ms tick = 50 one-millisecond substeps, no external drive. */
    private static void tick(CircuitSim sim) {
        for (int s = 0; s < SUBSTEPS_PER_TICK; s++) {
            sim.step(null);
        }
    }

    /**
     * Generates a valid XML string for the CircuitSim parser.
     * Requires lane0.out through lane3.out.
     */
    private String generateSyntheticCircuit(int count, int synapsesPerNeuron) {
        StringBuilder sb = new StringBuilder();
        sb.append("<hemibrain>\n");

        // 1. Required lane outputs
        for (int i = 0; i < 4; i++) {
            sb.append(String.format(Locale.ROOT, "  <neuron id=\"lane%d.out\"/>\n", i));
        }

        // 2. Generate the rest of the neurons
        for (int i = 4; i < count; i++) {
            sb.append(String.format(Locale.ROOT, "  <neuron id=\"n%d\"/>\n", i));
        }

        // 3. Generate connections (ring topology)
        for (int i = 0; i < count; i++) {
            String from = (i < 4) ? "lane" + i + ".out" : "n" + i;
            for (int j = 1; j <= synapsesPerNeuron; j++) {
                int targetIdx = (i + j) % count;
                String to = (targetIdx < 4) ? "lane" + targetIdx + ".out" : "n" + targetIdx;
                double weight = 0.1 + (j % 10) * 0.1;
                // ConnectomeXml requires delayMs > 0, so 1..10 ms (was 0..9).
                double delay = 1.0 + (j % 10) * 1.0;
                sb.append(String.format(Locale.ROOT, "  <connection from=\"%s\" to=\"%s\" weight=\"%.2f\" delayMs=\"%.1f\"/>\n", from, to, weight, delay));
            }
        }

        sb.append("</hemibrain>\n");
        return sb.toString();
    }
}
