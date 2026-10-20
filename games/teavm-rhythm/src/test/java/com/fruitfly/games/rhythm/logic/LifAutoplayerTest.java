package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class LifAutoplayerTest {

    private static final long SEED = 2026;

    /** Result of a full autoplayed song: [score, perfect, great, good, miss, spikes, maxCombo]. */
    private static long[] play(long seed, long frameMs) {
        RhythmGame g = new RhythmGame(NoteChart.generate(seed, 64, 120, 2000));
        LifAutoplayer p = new LifAutoplayer(g);
        long end = g.chart().lastNoteMs() + 1000;
        for (long t = 0; t <= end; t += frameMs) {
            p.advanceTo(t); // brain first, then the game clock, as in the browser loop
            g.update(t);
        }
        p.advanceTo(end);
        g.update(end);
        assertTrue(g.isFinished());
        return new long[] {g.score(), g.perfectCount(), g.greatCount(), g.goodCount(),
            g.missCount(), p.spikeCount(), g.maxCombo()};
    }

    @Test
    void latencyIsMeasuredFromTheNeuron() {
        assertEquals(3, LifAutoplayer.measureLatencyMs());
    }

    @Test
    void hitsMostNotesForSeed2026() {
        long[] r = play(SEED, 16);
        long hits = r[1] + r[2] + r[3];
        assertTrue(hits >= 58, "hit " + hits + "/64"); // "most" = at least 90%
        assertEquals(64, hits); // actual: every note, all PERFECT
        assertEquals(64, r[1]);
        assertEquals(0, r[4]);
        assertEquals(64, r[6]);
        assertEquals(58_800, r[0]);
    }

    @Test
    void deterministicAcrossRunsAndFrameRates() {
        long[] a = play(SEED, 16);
        long[] b = play(SEED, 16);
        long[] c = play(SEED, 7);
        long[] d = play(SEED, 1000);
        for (int i = 0; i < a.length; i++) {
            assertEquals(a[i], b[i], "repeat run, field " + i);
            assertEquals(a[i], c[i], "7 ms frames, field " + i);
            assertEquals(a[i], d[i], "1 s frames, field " + i);
        }
    }

    @Test
    void otherSeedsAlsoMostlyHit() {
        for (long seed : new long[] {1, 7, 42, 99, 123456789L}) {
            long[] r = play(seed, 16);
            assertTrue(r[1] + r[2] + r[3] >= 58, "seed " + seed + " hit " + (r[1] + r[2] + r[3]));
        }
    }

    @Test
    void brainAdvancesInWholeTicks() {
        RhythmGame g = new RhythmGame(NoteChart.generate(SEED, 8, 120, 2000));
        LifAutoplayer p = new LifAutoplayer(g);
        p.advanceTo(49);
        assertEquals(0, p.brainTimeMs());
        p.advanceTo(50);
        assertEquals(50, p.brainTimeMs());
        p.advanceTo(1234);
        assertEquals(1200, p.brainTimeMs());
        assertEquals(0, p.spikeCount()); // first note at 2000 ms: no drive yet
    }
}
