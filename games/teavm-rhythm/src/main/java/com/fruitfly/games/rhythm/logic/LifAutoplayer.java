package com.fruitfly.games.rhythm.logic;

import java.util.List;

/**
 * Four-neuron LIF autoplayer: one {@link LifNeuron} per lane.
 *
 * Each lane's next note drives that lane's neuron: when the song clock reaches
 * noteTime - latency, the neuron receives one conductance pulse of
 * {@link #DRIVE_G}. The neuron integrates it with RK4 and, if it crosses
 * threshold in some 1 ms substep, that spike is a key press in the lane at
 * that substep's time. Nothing else presses keys, so the score comes only
 * from spikes. The latency is measured once, by running a fresh neuron with
 * the same pulse, so with no interference the spike lands on the note.
 *
 * Everything is deterministic: there's no randomness and no wall clock. The
 * brain advances in whole 50 ms ticks of 50 substeps, as in LIFRK4.
 */
public final class LifAutoplayer {
    /**
     * Pulse size. From rest, a pulse G peaks at about 0.1575 G above V_REST
     * (tau_v = 20, tau_g = 5), so G must exceed ~44.4 to cross the 7 mV
     * threshold gap. 60 crosses after a few ms of integration.
     */
    public static final double DRIVE_G = 60.0;

    private final RhythmGame game;
    private final long aimMs;
    private final PressSink sink;
    private final LifNeuron[] neurons = new LifNeuron[RhythmGame.LANES];
    private final int[] nextNoteIndex = new int[RhythmGame.LANES];
    private final long latencyMs;
    private long substepsDone;
    private int spikes;

    public LifAutoplayer(RhythmGame game) {
        this(game, 0, null);
    }

    /**
     * @param aimMs offset from the note time the spike is aimed at (0 = on the note; assist mode aims late)
     * @param sink  where spikes go as presses; null = straight to {@code game.press}
     */
    public LifAutoplayer(RhythmGame game, long aimMs, PressSink sink) {
        this.game = game;
        this.aimMs = aimMs;
        this.sink = sink;
        for (int l = 0; l < RhythmGame.LANES; l++) {
            neurons[l] = new LifNeuron();
            nextNoteIndex[l] = advanceIndex(l, 0);
        }
        this.latencyMs = measureLatencyMs();
    }

    /** Substeps from the pulse to the first spike for a neuron at rest (1 ms each). */
    static long measureLatencyMs() {
        LifNeuron n = new LifNeuron();
        for (int s = 0; s < 1000; s++) {
            if (n.substep(s == 0 ? DRIVE_G : 0.0, LifNeuron.DT_MS)) {
                return s;
            }
        }
        throw new IllegalStateException("DRIVE_G never reaches threshold");
    }

    public long latencyMs() {
        return latencyMs;
    }

    public int spikeCount() {
        return spikes;
    }

    /** Song time the brain has simulated up to, in ms (a multiple of 50). */
    public long brainTimeMs() {
        return (long) (substepsDone * LifNeuron.DT_MS);
    }

    public LifNeuron neuron(int lane) {
        return neurons[lane];
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
        for (int s = 0; s < LifNeuron.SUBSTEPS; s++) {
            long t = (long) (substepsDone * LifNeuron.DT_MS);
            for (int l = 0; l < RhythmGame.LANES; l++) {
                double drive = 0.0;
                int idx = nextNoteIndex[l];
                if (idx < notes.size() && t >= notes.get(idx).timeMs() + aimMs - latencyMs) {
                    drive = DRIVE_G;
                    nextNoteIndex[l] = advanceIndex(l, idx + 1);
                }
                if (neurons[l].substep(drive, LifNeuron.DT_MS)) {
                    spikes++;
                    if (sink == null) {
                        game.press(l, t);
                    } else {
                        sink.press(l, t);
                    }
                }
            }
            substepsDone++;
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
