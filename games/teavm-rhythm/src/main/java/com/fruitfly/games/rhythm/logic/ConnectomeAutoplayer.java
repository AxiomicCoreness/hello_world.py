package com.fruitfly.games.rhythm.logic;

import java.util.List;

/**
 * Connectome-driven autoplayer: the chart cue for lane L drives neuron
 * {@code laneL.in} of a {@link Circuit}; the signal travels through the
 * circuit's weighted, delayed synapses ({@link CircuitSim}, LifNeuron math,
 * SovereignAutomaton's delivery timing); a spike of {@code laneL.out} is a
 * key press in lane L at that substep's time. Nothing else presses keys.
 *
 * As in {@link LifAutoplayer}, the cue is one {@link LifAutoplayer#DRIVE_G}
 * pulse sent latency(L) ms before the note, where latency(L) is measured
 * once by cueing lane L alone in a fresh copy of the circuit. Deterministic:
 * no randomness, no wall clock, whole 50 ms brain ticks.
 *
 * The shipped circuit (connectomes/toy_lane_circuit.xml) is a TOY example,
 * not the Drosophila connectome.
 */
public final class ConnectomeAutoplayer {
    public static final int MAX_LATENCY_MS = 1000;

    private final RhythmGame game;
    private final long aimMs;
    private final PressSink sink;
    private final CircuitSim sim;
    private final int[] inputs = new int[RhythmGame.LANES];
    private final int[] outputs = new int[RhythmGame.LANES];
    private final long[] latency = new long[RhythmGame.LANES];
    private final int[] nextNoteIndex = new int[RhythmGame.LANES];
    private final CueProbe probe;
    private int presses;

    public ConnectomeAutoplayer(RhythmGame game, Circuit circuit) {
        this(game, circuit, 0, null);
    }

    /**
     * @param aimMs offset from the note time the output spike is aimed at (0 = on the note)
     * @param sink  where output spikes go as presses; null = straight to {@code game.press}
     */
    public ConnectomeAutoplayer(RhythmGame game, Circuit circuit, long aimMs, PressSink sink) {
        this.game = game;
        this.aimMs = aimMs;
        this.sink = sink;
        int[][] io = resolveLanes(circuit);
        for (int l = 0; l < RhythmGame.LANES; l++) {
            inputs[l] = io[0][l];
            outputs[l] = io[1][l];
            latency[l] = measureLatencyMs(circuit, l);
        }
        this.sim = new CircuitSim(circuit);
        for (int l = 0; l < RhythmGame.LANES; l++) {
            nextNoteIndex[l] = advanceIndex(l, 0);
        }
        this.probe = new CueProbe(game.chart().notes().size());
    }

    /** Per-note cue / peak voltage / spike record of each lane's motor neuron laneN.out (moves list). */
    public CueProbe probe() {
        return probe;
    }

    public static String inputId(int lane) {
        return "lane" + lane + ".in";
    }

    public static String outputId(int lane) {
        return "lane" + lane + ".out";
    }

    /** [0] = input index per lane, [1] = output index per lane. */
    static int[][] resolveLanes(Circuit c) {
        int[][] io = new int[2][RhythmGame.LANES];
        for (int l = 0; l < RhythmGame.LANES; l++) {
            io[0][l] = c.indexOf(inputId(l));
            io[1][l] = c.indexOf(outputId(l));
            if (io[0][l] < 0) {
                throw new IllegalArgumentException("connectome has no input neuron '" + inputId(l) + "'");
            }
            if (io[1][l] < 0) {
                throw new IllegalArgumentException("connectome has no output neuron '" + outputId(l) + "'");
            }
        }
        return io;
    }

    /** Substeps from cueing lane's input (alone, fresh circuit) to its output's first spike. */
    public static long measureLatencyMs(Circuit c, int lane) {
        int[][] io = resolveLanes(c);
        CircuitSim s = new CircuitSim(c);
        double[] ext = new double[c.neuronCount()];
        for (int t = 0; t < MAX_LATENCY_MS; t++) {
            ext[io[0][lane]] = t == 0 ? LifAutoplayer.DRIVE_G : 0.0;
            if (s.step(ext)[io[1][lane]]) {
                return t;
            }
        }
        throw new IllegalArgumentException("lane " + lane + ": cue never reaches '" + outputId(lane)
                + "' within " + MAX_LATENCY_MS + " ms");
    }

    /** Lane label from the output neuron's region, or null if it has none. */
    public static String laneLabel(Circuit c, int lane) {
        int o = c.indexOf(outputId(lane));
        return o < 0 ? null : c.region(o);
    }

    public long latencyMs(int lane) {
        return latency[lane];
    }

    public CircuitSim sim() {
        return sim;
    }

    /** All spikes in the circuit. */
    public long spikeCount() {
        return sim.spikeCount();
    }

    /** Output spikes, i.e. key presses. */
    public int pressCount() {
        return presses;
    }

    public long brainTimeMs() {
        return (long) (sim.substeps() * LifNeuron.DT_MS);
    }

    /** Run whole brain ticks until brain time would pass {@code songMs}. */
    public void advanceTo(long songMs) {
        long tickMs = (long) LifNeuron.BRAIN_TICK_MS;
        while (brainTimeMs() + tickMs <= songMs) {
            tick();
        }
    }

    private void tick() {
        List<Note> notes = game.chart().notes();
        double[] ext = new double[sim.circuit().neuronCount()];
        for (int s = 0; s < LifNeuron.SUBSTEPS; s++) {
            long t = brainTimeMs();
            for (int l = 0; l < RhythmGame.LANES; l++) {
                ext[inputs[l]] = 0.0;
            }
            for (int l = 0; l < RhythmGame.LANES; l++) {
                int idx = nextNoteIndex[l];
                if (idx < notes.size() && t >= notes.get(idx).timeMs() + aimMs - latency[l]) {
                    ext[inputs[l]] += LifAutoplayer.DRIVE_G;
                    probe.cue(l, idx, t, latency[l]);
                    nextNoteIndex[l] = advanceIndex(l, idx + 1);
                }
            }
            boolean[] spiked = sim.step(ext);
            for (int l = 0; l < RhythmGame.LANES; l++) {
                probe.sample(l, t, sim.neuron(outputs[l]).vBeforeReset(), spiked[outputs[l]]);
                if (spiked[outputs[l]]) {
                    presses++;
                    if (sink == null) {
                        game.press(l, t, true);
                    } else {
                        sink.press(l, t);
                    }
                }
            }
        }
    }

    private int advanceIndex(int lane, int from) {
        List<Note> notes = game.chart().notes();
        int i = from;
        while (i < notes.size() && notes.get(i).lane() != lane) {
            i++;
        }
        return i;
    }
}
