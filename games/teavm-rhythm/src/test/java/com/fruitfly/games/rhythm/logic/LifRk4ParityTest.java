package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/**
 * Parity between the game's {@link LifNeuron} port and the real root
 * com.fruitfly.brain.LIFRK4, using golden traces that
 * tools/LifGoldenTraceGen.java generated from LIFRK4 itself
 * (src/test/resources/lif_rk4_golden_traces.txt). Every substep's v, g and
 * refractoryRemaining must match to 1e-12, and so must the spike substeps.
 * If LIFRK4 changes, regenerate the traces (see README) and this fails until
 * the port is updated.
 */
class LifRk4ParityTest {
    private static final double TOL = 1e-12;
    private static final String RESOURCE = "/lif_rk4_golden_traces.txt";

    private static String source;
    private static final Map<String, String> CONSTS = new HashMap<>();
    private static final List<Trace> TRACES = new ArrayList<>();

    /** One substep's expected state. */
    private static final class State {
        final int tick;
        final int sub;
        final double v;
        final double g;
        final double refr;
        final boolean spike;

        State(String[] p) {
            tick = Integer.parseInt(p[1]);
            sub = Integer.parseInt(p[2]);
            v = Double.parseDouble(p[3]);
            g = Double.parseDouble(p[4]);
            refr = Double.parseDouble(p[5]);
            spike = "1".equals(p[6]);
        }
    }

    private static final class Trace {
        final String name;
        final boolean legacy;
        final List<double[]> inputs = new ArrayList<>();   // per-substep mode
        final List<Double> deltas = new ArrayList<>();     // legacy mode
        final List<State> states = new ArrayList<>();
        final List<double[]> after = new ArrayList<>();    // legacy: v, g, refr after each tick

        Trace(String name, boolean legacy) {
            this.name = name;
            this.legacy = legacy;
        }
    }

    @BeforeAll
    static void load() throws IOException {
        InputStream in = LifRk4ParityTest.class.getResourceAsStream(RESOURCE);
        assertNotNull(in, RESOURCE + " missing: run tools/regen-lif-traces.sh");
        Trace cur = null;
        try (BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) {
                if (line.isEmpty() || line.startsWith("#")) {
                    continue;
                }
                String[] p = line.split(" ");
                switch (p[0]) {
                    case "source":
                        source = line.substring(7);
                        break;
                    case "const":
                        CONSTS.put(p[1], p[2]);
                        break;
                    case "trace":
                        cur = new Trace(p[1], "legacy".equals(p[2]));
                        TRACES.add(cur);
                        break;
                    case "in":
                        double[] row = new double[p.length - 2];
                        for (int i = 0; i < row.length; i++) {
                            row[i] = Double.parseDouble(p[i + 2]);
                        }
                        cur.inputs.add(row);
                        break;
                    case "delta":
                        cur.deltas.add(Double.parseDouble(p[2]));
                        break;
                    case "s":
                        cur.states.add(new State(p));
                        break;
                    case "after":
                        cur.after.add(new double[] {Double.parseDouble(p[2]), Double.parseDouble(p[3]),
                            Double.parseDouble(p[4])});
                        break;
                    case "end":
                        cur = null;
                        break;
                    default:
                        throw new IllegalStateException("bad line: " + line);
                }
            }
        }
    }

    @Test
    void tracesComeFromRootLifRk4() {
        assertNotNull(source);
        assertTrue(source.startsWith("src/main/java/com/fruitfly/brain/LIFRK4.java"), source);
        assertEquals(6, TRACES.size());
    }

    @Test
    void constantsMirrorLifRk4Exactly() {
        assertEquals(LifNeuron.V_REST, Double.parseDouble(CONSTS.get("V_REST")));
        assertEquals(LifNeuron.V_THRESH, Double.parseDouble(CONSTS.get("V_THRESH")));
        assertEquals(LifNeuron.V_RESET, Double.parseDouble(CONSTS.get("V_RESET")));
        assertEquals(LifNeuron.TAU_V, Double.parseDouble(CONSTS.get("TAU_V")));
        assertEquals(LifNeuron.TAU_G, Double.parseDouble(CONSTS.get("TAU_G")));
        assertEquals(LifNeuron.REFRAC, Double.parseDouble(CONSTS.get("REFRAC")));
        assertEquals(LifNeuron.SYNAPTIC_GAIN, Double.parseDouble(CONSTS.get("SYNAPTIC_GAIN")));
        assertEquals(LifNeuron.BRAIN_TICK_MS, Double.parseDouble(CONSTS.get("BRAIN_TICK_MS")));
        assertEquals(LifNeuron.SUBSTEPS, Integer.parseInt(CONSTS.get("SUBSTEPS")));
    }

    @Test
    void everySubstepMatchesTheRealLifRk4() {
        int checked = 0;
        int spikes = 0;
        for (Trace t : TRACES) {
            LifNeuron n = new LifNeuron();
            int k = 0;
            int ticks = t.legacy ? t.deltas.size() : t.inputs.size();
            for (int tick = 0; tick < ticks; tick++) {
                for (int s = 0; s < LifNeuron.SUBSTEPS; s++) {
                    double in;
                    if (t.legacy) {
                        // stepTick(double) adds the delta after tick-1, i.e. before substep 0 of this tick
                        in = (s == 0 && tick > 0) ? t.deltas.get(tick - 1) : 0.0;
                    } else {
                        in = t.inputs.get(tick)[s];
                    }
                    boolean spiked = n.substep(in, LifNeuron.DT_MS);
                    State e = t.states.get(k++);
                    String at = t.name + " tick " + tick + " substep " + s;
                    assertEquals(tick, e.tick, at);
                    assertEquals(s, e.sub, at);
                    assertEquals(e.v, n.v(), TOL, "v @ " + at);
                    assertEquals(e.g, n.g(), TOL, "g @ " + at);
                    assertEquals(e.refr, n.refractoryRemaining(), TOL, "refractory @ " + at);
                    assertEquals(e.spike, spiked, "spike @ " + at);
                    checked++;
                    if (spiked) {
                        spikes++;
                    }
                }
            }
            assertEquals(t.states.size(), k, t.name);
        }
        assertEquals(6 * 4 * 50, checked);
        assertEquals(15, spikes); // golden file has 15 spike substeps
    }

    @Test
    void publicStepTickApisMatchTickBoundaries() {
        for (Trace t : TRACES) {
            LifNeuron n = new LifNeuron();
            if (t.legacy) {
                for (int tick = 0; tick < t.deltas.size(); tick++) {
                    n.stepTick(t.deltas.get(tick));
                    double[] e = t.after.get(tick);
                    assertEquals(e[0], n.v(), TOL, t.name + " v after tick " + tick);
                    assertEquals(e[1], n.g(), TOL, t.name + " g after tick " + tick);
                    assertEquals(e[2], n.refractoryRemaining(), TOL, t.name + " refr after tick " + tick);
                }
            } else {
                for (int tick = 0; tick < t.inputs.size(); tick++) {
                    n.stepTick(t.inputs.get(tick));
                    State e = t.states.get(tick * LifNeuron.SUBSTEPS + LifNeuron.SUBSTEPS - 1);
                    assertEquals(e.v, n.v(), TOL, t.name + " v end of tick " + tick);
                    assertEquals(e.g, n.g(), TOL, t.name + " g end of tick " + tick);
                    assertEquals(e.refr, n.refractoryRemaining(), TOL, t.name + " refr end of tick " + tick);
                }
            }
        }
    }

    @Test
    void refractoryRoundingIsMirrored() {
        // 2.2 - 1 - 1 in doubles is 0.20000000000000018, then clamped to exactly 0
        Trace t = TRACES.stream().filter(x -> x.name.equals("pulse500_mid_tick")).findFirst().orElseThrow();
        State spike = t.states.get(17);
        assertTrue(spike.spike);
        assertEquals(2.2, t.states.get(17).refr);
        assertEquals(2.2 - 1.0 - 1.0, t.states.get(19).refr);
        assertEquals(0.20000000000000018, t.states.get(19).refr);
        assertEquals(0.0, t.states.get(20).refr);
    }
}
