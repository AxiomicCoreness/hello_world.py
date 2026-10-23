package com.fruitfly.games.rhythm.logic;

/**
 * Records, per note, what the fly's lane motor neuron did after that note's
 * cue: the cue time, the peak membrane voltage in the cue window (read before
 * a spike resets it, {@link LifNeuron#vBeforeReset()}) and the first spike.
 * Observation only: the autoplayers call {@link #cue} and {@link #sample} and
 * nothing here feeds back into the brain.
 *
 * Cue window for a note cued at c in a lane with latency L: substeps
 * c .. c + L + {@link Judgement#MAX_WINDOW_MS}. Open windows in a lane are
 * served first-in first-out, the way {@link RhythmGame#press} judges the
 * earliest open note: only the oldest open window samples the voltage, and a
 * spike belongs to it and closes it. So when two cues in one lane overlap,
 * the second note's window starts collecting once the first one is served.
 */
public final class CueProbe {
    private final long[] cueMs;
    private final double[] peakV;
    private final long[] spikeMs;
    private static final int QUEUE = 16;
    private final int[][] open = new int[RhythmGame.LANES][QUEUE];
    private final long[][] openUntil = new long[RhythmGame.LANES][QUEUE];
    private final int[] head = new int[RhythmGame.LANES];
    private final int[] count = new int[RhythmGame.LANES];

    public CueProbe(int noteCount) {
        cueMs = new long[noteCount];
        peakV = new double[noteCount];
        spikeMs = new long[noteCount];
        for (int i = 0; i < noteCount; i++) {
            cueMs[i] = Long.MIN_VALUE;
            peakV[i] = Double.NEGATIVE_INFINITY;
            spikeMs[i] = Long.MIN_VALUE;
        }
    }

    /** Note {@code idx} in {@code lane} is cued at substep time {@code t}; its window lasts latency + 150 ms. */
    void cue(int lane, int idx, long t, long latencyMs) {
        if (idx < 0 || idx >= cueMs.length) {
            return;
        }
        if (count[lane] == QUEUE) { // more than 16 overlapping cues in one lane: drop the oldest
            head[lane] = (head[lane] + 1) % QUEUE;
            count[lane]--;
        }
        int slot = (head[lane] + count[lane]) % QUEUE;
        open[lane][slot] = idx;
        openUntil[lane][slot] = t + latencyMs + Judgement.MAX_WINDOW_MS;
        count[lane]++;
        cueMs[idx] = t;
    }

    /** After a substep at time t: the lane neuron's pre-reset voltage and whether it spiked. */
    void sample(int lane, long t, double vBeforeReset, boolean spiked) {
        while (count[lane] > 0 && t > openUntil[lane][head[lane]]) {
            head[lane] = (head[lane] + 1) % QUEUE;
            count[lane]--;
        }
        if (count[lane] == 0) {
            return;
        }
        int idx = open[lane][head[lane]];
        if (vBeforeReset > peakV[idx]) {
            peakV[idx] = vBeforeReset;
        }
        if (spiked) {
            spikeMs[idx] = t;
            head[lane] = (head[lane] + 1) % QUEUE;
            count[lane]--;
        }
    }

    public int size() {
        return cueMs.length;
    }

    public boolean wasCued(int idx) {
        return cueMs[idx] != Long.MIN_VALUE;
    }

    /** Cue time of note idx (Long.MIN_VALUE if never cued). */
    public long cueMs(int idx) {
        return cueMs[idx];
    }

    /** Peak pre-reset membrane voltage in note idx's cue window, mV (-Infinity if never cued). */
    public double peakV(int idx) {
        return peakV[idx];
    }

    public boolean fired(int idx) {
        return spikeMs[idx] != Long.MIN_VALUE;
    }

    /** Time of the first spike in the window (Long.MIN_VALUE if none). */
    public long spikeMs(int idx) {
        return spikeMs[idx];
    }
}
