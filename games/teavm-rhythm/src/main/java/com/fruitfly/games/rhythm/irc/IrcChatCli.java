package com.fruitfly.games.rhythm.logic;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class CircuitSimSmokeTest {

    private static final int NEURONS = 1000;
    private static final int SYNAPSES_PER_NEURON = 20;
    private static final int TICKS = 10; // 10 ticks * 50ms = 0.5s of simulation

    @Test
    public void test1000NeuronSmoke() {
        String xml = generateSyntheticCircuit(NEURONS, SYNAPSES_PER_NEURON);
        InputStream is = new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8));

        CircuitSim sim = null;
        long startLoad = System.nanoTime();
        try {
            // Assuming the parser is called ConnectomeXml and returns a CircuitSim
            // Adjust the parser class name and method to match your actual code
            sim = ConnectomeXml.parse(is, "synthetic_" + NEURONS + ".xml");
        } catch (Exception e) {
            fail("Parser threw exception: " + e.getMessage());
        }
        long endLoad = System.nanoTime();
        double loadMs = (endLoad - startLoad) / 1_000_000.0;

        assertNotNull(sim, "CircuitSim is null");
        assertEquals(NEURONS, sim.neuronCount(), "Loaded neuron count mismatch");
        assertEquals(NEURONS * SYNAPSES_PER_NEURON, sim.synapseCount(), "Loaded synapse count mismatch");

        System.out.println("Load time for " + NEURONS + " neurons: " + loadMs + " ms");
        assertTrue(loadMs < 2000, "Loading 1000 neurons took longer than 2 seconds (possible O(N^2) bottleneck)");

        // Warmup
        for (int i = 0; i < 2; i++) {
            sim.step();
        }

        // Measured run
        long startSim = System.nanoTime();
        for (int i = 0; i < TICKS; i++) {
            sim.step();
        }
        long endSim = System.nanoTime();
        double totalSimMs = (endSim - startSim) / 1_000_000.0;
        double msPerTick = totalSimMs / TICKS;

        System.out.printf("Simulation time: %.2f ms/tick (%.1f fps)%n", msPerTick, 1000.0 / msPerTick);
        
        // The 50ms budget check
        if (msPerTick > 50.0) {
            System.out.println("⚠️ WARNING: Exceeds 50ms frame budget!");
        } else {
            System.out.println("✅ Within 50ms frame budget.");
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
            sb.append(String.format("  <neuron id=\"lane%d.out\"/>\n", i));
        }

        // 2. Generate the rest of the neurons
        for (int i = 4; i < count; i++) {
            sb.append(String.format("  <neuron id=\"n%d\"/>\n", i));
        }

        // 3. Generate connections (ring topology)
        for (int i = 0; i < count; i++) {
            String from = (i < 4) ? "lane" + i + ".out" : "n" + i;
            for (int j = 1; j <= synapsesPerNeuron; j++) {
                int targetIdx = (i + j) % count;
                String to = (targetIdx < 4) ? "lane" + targetIdx + ".out" : "n" + targetIdx;
                double weight = 0.1 + (j % 10) * 0.1;
                double delay = (j % 10) * 1.0;
                sb.append(String.format("  <connection from=\"%s\" to=\"%s\" weight=\"%.2f\" delayMs=\"%.1f\"/>\n", from, to, weight, delay));
            }
        }

        sb.append("</hemibrain>\n");
        return sb.toString();
    }
}
