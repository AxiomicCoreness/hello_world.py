package com.fruitfly.games.rhythm.logic;

/**
 * Observation-only record of recent spike times per lane neuron, so the CLI
 * can summarise what the fly brain actually did in the last N ms (the LLM
 * chat's neuron snapshot). The autoplayers call {@link #record} when a lane
 * neuron spikes; nothing here feeds back into the brain.
 *
 * Each lane keeps a ring of the last {@link #CAPACITY} spike times (song ms,
 * 1 ms substep grid). Older spikes are overwritten; a window query only ever
 * counts spikes still in the ring.
 */
public final class SpikeWindow {
    public static final int CAPACITY = 64;

    private final long[][] times;
    private final int[] head;
    private final int[] count;
    private final long[] total;

    public SpikeWindow(int lanes) {
        times = new long[lanes][CAPACITY];
        head = new int[lanes];
        count = new int[lanes];
        total = new long[lanes];
    }

    public int lanes() {
        return times.length;
    }

    /** Lane {@code lane} spiked at song time {@code tMs}. */
    public void record(int lane, long tMs) {
        if (count[lane] == CAPACITY) { // full: overwrite the oldest
            times[lane][head[lane]] = tMs;
            head[lane] = (head[lane] + 1) % CAPACITY;
        } else {
            times[lane][(head[lane] + count[lane]) % CAPACITY] = tMs;
            count[lane]++;
        }
        total[lane]++;
    }

    /** Spikes in lane with time in (nowMs - windowMs, nowMs]. */
    public int countInWindow(int lane, long nowMs, long windowMs) {
        int n = 0;
        for (int k = 0; k < count[lane]; k++) {
            long t = times[lane][(head[lane] + k) % CAPACITY];
            if (t > nowMs - windowMs && t <= nowMs) {
                n++;
            }
        }
        return n;
    }

    /** Most recent spike time in lane, or Long.MIN_VALUE if it never spiked. */
    public long lastSpikeMs(int lane) {
        if (count[lane] == 0) {
            return Long.MIN_VALUE;
        }
        return times[lane][(head[lane] + count[lane] - 1) % CAPACITY];
    }

    /** All spikes ever recorded in lane (not just the ring). */
    public long total(int lane) {
        return total[lane];
    }
}
