package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class SongClockTest {

    @Test
    void zeroBeforeStart() {
        SongClock c = new SongClock(25);
        assertEquals(0.0, c.sample(5000, true, 1234), 0.0);
        assertEquals(0L, c.nowMs());
        assertFalse(c.isStarted());
    }

    @Test
    void noAudioMatchesOriginalFrameClock() {
        SongClock c = new SongClock(40); // offset only applies to audio
        c.start(1000.5, false);
        assertEquals(0L, (long) c.sample(1000.5, false, 0));
        c.sample(3017.9, false, 0);
        assertEquals((long) (3017.9 - 1000.5), c.nowMs());
        assertFalse(c.isAudioMode());
    }

    @Test
    void audioModeReadsPositionPlusOffsetEachSample() {
        SongClock c = new SongClock(30);
        c.start(0, true);
        assertTrue(c.isAudioMode());
        // frame stamps deliberately unrelated to audio: audio wins
        assertEquals(30.0, c.sample(99999, true, 0.0), 0.0);
        assertEquals(1030.25, c.sample(5, true, 1000.25), 1e-12);
        assertEquals(1030L, c.nowMs());
    }

    @Test
    void noDriftFromManySmallFrames() {
        // 10,000 frames of 16.6667 ms: a per-frame truncated delta would lose up to ~6.7 s; absolute reads lose nothing.
        SongClock c = new SongClock(0);
        c.start(0, true);
        double pos = 0;
        long truncatedSum = 0;
        double prev = 0;
        for (int i = 0; i < 10_000; i++) {
            pos = (i + 1) * (1000.0 / 60.0);
            c.sample(i, true, pos);
            truncatedSum += (long) (pos - prev);
            prev = pos;
        }
        assertEquals((long) Math.floor(pos), c.nowMs());
        assertTrue((long) pos - truncatedSum > 6000, "truncating per-frame deltas would drift");
    }

    @Test
    void fallsBackToFrameClockWhenAudioDrops() {
        SongClock c = new SongClock(0);
        c.start(100, true);
        c.sample(200, true, 1500);      // last good audio reading at stamp 200
        assertEquals(1500.0, c.now(), 0.0);
        c.sample(250, false, 0);        // audio failed: continue from 1500 on the frame clock
        assertEquals(1550.0, c.now(), 0.0);
        assertFalse(c.isAudioMode());
        c.sample(300, true, 0);         // stays on the frame clock even if audio claims ok later
        assertEquals(1600.0, c.now(), 0.0);
    }

    @Test
    void audioFailingBeforeAnyReadingIsTheOriginalClock() {
        SongClock c = new SongClock(500);
        c.start(1000, true);
        c.sample(1600, false, 0);
        assertEquals(600L, c.nowMs());
    }

    @Test
    void neverGoesBackwards() {
        SongClock c = new SongClock(0);
        c.start(0, true);
        c.sample(0, true, 800);
        c.sample(16, true, 790);  // audio jitter / seek back
        assertEquals(800.0, c.now(), 0.0);
        SongClock neg = new SongClock(-200);
        neg.start(0, true);
        assertEquals(0.0, neg.sample(0, true, 50), 0.0); // 50 - 200 < 0 clamps to 0
        assertEquals(100.0, neg.sample(0, true, 300), 0.0);
    }

    @Test
    void floorNeverJudgesEarly() {
        SongClock c = new SongClock(0);
        c.start(0, true);
        c.sample(0, true, 999.9999);
        assertEquals(999L, c.nowMs());
        c.stop();
        assertEquals(0L, c.nowMs());
        assertFalse(c.isAudioMode());
    }
}
