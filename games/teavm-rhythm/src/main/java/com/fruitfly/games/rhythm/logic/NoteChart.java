package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Deterministic note chart. Uses its own 64-bit LCG (Knuth MMIX constants)
 * instead of java.util.Random so the chart is bit-identical on the JVM and in
 * TeaVM-compiled JavaScript for the same seed.
 */
public final class NoteChart {
    private final long seed;
    private final List<Note> notes;

    private NoteChart(long seed, List<Note> notes) {
        this.seed = seed;
        this.notes = Collections.unmodifiableList(notes);
    }

    public long seed() {
        return seed;
    }

    public List<Note> notes() {
        return notes;
    }

    /** Song length: last note time (0 for an empty chart). */
    public long lastNoteMs() {
        return notes.isEmpty() ? 0 : notes.get(notes.size() - 1).timeMs();
    }

    /**
     * Generate {@code count} notes at {@code bpm}, starting at {@code leadInMs}.
     * Each step advances by a half or full beat (8th/quarter notes); lanes are
     * chosen so the same lane never repeats more than twice in a row.
     */
    public static NoteChart generate(long seed, int count, int bpm, long leadInMs) {
        if (count < 0) {
            throw new IllegalArgumentException("count must be >= 0");
        }
        if (bpm <= 0 || bpm > 400) {
            throw new IllegalArgumentException("bpm out of range: " + bpm);
        }
        if (leadInMs < 0) {
            throw new IllegalArgumentException("leadInMs must be >= 0");
        }
        Lcg rng = new Lcg(seed);
        long halfBeatMs = 30_000L / bpm;
        List<Note> out = new ArrayList<>(count);
        long t = leadInMs;
        int prevLane = -1;
        int run = 0;
        for (int i = 0; i < count; i++) {
            int lane = rng.nextInt(RhythmGame.LANES);
            if (lane == prevLane && run >= 2) {
                lane = (lane + 1 + rng.nextInt(RhythmGame.LANES - 1)) % RhythmGame.LANES;
            }
            run = lane == prevLane ? run + 1 : 1;
            prevLane = lane;
            out.add(new Note(lane, t));
            t += halfBeatMs * (rng.nextInt(4) == 0 ? 2 : 1);
        }
        return new NoteChart(seed, out);
    }

    /** Fresh copy of the same notes, unresolved, for a restart. */
    public NoteChart fresh() {
        List<Note> copy = new ArrayList<>(notes.size());
        for (Note n : notes) {
            copy.add(new Note(n.lane(), n.timeMs()));
        }
        return new NoteChart(seed, copy);
    }

    /** Minimal deterministic 64-bit LCG. */
    static final class Lcg {
        private long state;

        Lcg(long seed) {
            state = seed ^ 0x5DEECE66DL;
        }

        long nextLong() {
            state = state * 6364136223846793005L + 1442695040888963407L;
            return state;
        }

        /** Uniform-ish int in [0, bound) from the high 31 bits. */
        int nextInt(int bound) {
            if (bound <= 0) {
                throw new IllegalArgumentException("bound must be > 0");
            }
            int hi = (int) (nextLong() >>> 33);
            return hi % bound;
        }
    }
}
