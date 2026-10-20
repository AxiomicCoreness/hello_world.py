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

    /**
     * Chart from explicit notes (e.g. a loaded JSON chart). The notes are copied
     * unresolved and stably sorted by time, so equal times keep their input
     * order. Two notes in the same lane at the same time are rejected, because
     * one press can only hit one of them. {@link #seed()} is -1 for such charts.
     */
    public static NoteChart fromNotes(List<Note> notes) {
        if (notes == null) {
            throw new IllegalArgumentException("notes must not be null");
        }
        List<Note> copy = new ArrayList<>(notes.size());
        for (int i = 0; i < notes.size(); i++) {
            Note n = notes.get(i);
            if (n == null) {
                throw new IllegalArgumentException("note " + i + " is null");
            }
            copy.add(new Note(n.lane(), n.timeMs()));
        }
        // Insertion sort: stable, needs no Comparator lambdas, fine for chart sizes.
        for (int i = 1; i < copy.size(); i++) {
            Note x = copy.get(i);
            int j = i - 1;
            while (j >= 0 && copy.get(j).timeMs() > x.timeMs()) {
                copy.set(j + 1, copy.get(j));
                j--;
            }
            copy.set(j + 1, x);
        }
        for (int i = 1; i < copy.size(); i++) {
            Note cur = copy.get(i);
            for (int j = i - 1; j >= 0 && copy.get(j).timeMs() == cur.timeMs(); j--) {
                if (copy.get(j).lane() == cur.lane()) {
                    throw new IllegalArgumentException("duplicate note: lane " + cur.lane()
                            + " at " + cur.timeMs() + " ms appears twice");
                }
            }
        }
        return new NoteChart(-1L, copy);
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
