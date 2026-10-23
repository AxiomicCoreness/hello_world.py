package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** The smoothed audio clock: monotonic and smooth under coarse audio.currentTime updates (Safari-style steps). */
class SmoothClockTest {
    /** [mean, sd, min, max, maxAbsErrorAfterSettle, monotonic?1:0] of per-frame deltas, 60 fps, audio reported in stepMs steps. */
    static double[] run(boolean smooth, double stepMs, double frameMs, int frames) {
        SongClock c = new SongClock(0, smooth);
        c.start(0, true);
        double prev = Double.NaN;
        double sum = 0;
        double sq = 0;
        double min = 1e9;
        double max = -1e9;
        double err = 0;
        int n = 0;
        boolean mono = true;
        for (int i = 1; i <= frames; i++) {
            double stamp = i * frameMs;
            double reading = Math.floor(stamp / stepMs) * stepMs; // true time = stamp
            double t = c.sample(stamp, true, reading);
            if (i > 60) {
                double d = t - prev;
                sum += d;
                sq += d * d;
                min = Math.min(min, d);
                max = Math.max(max, d);
                n++;
                err = Math.max(err, Math.abs(t - stamp));
                if (d < 0) {
                    mono = false;
                }
            }
            prev = t;
        }
        double mean = sum / n;
        return new double[] {mean, Math.sqrt(Math.max(0, sq / n - mean * mean)), min, max, err, mono ? 1 : 0};
    }

    @Test
    void rawClockStepsUnderCoarseUpdates() {
        double[] r = run(false, 40, 1000 / 60.0, 600);
        assertTrue(r[1] > 10, "raw sd " + r[1]);
        assertEquals(0.0, r[2], 1e-9, "raw: some frames don't move at all");
    }

    @Test
    void smoothedClockIsMonotonicAndSmoothFor20To50MsSteps() {
        for (double step : new double[] {20, 25, 33, 40, 50}) {
            double[] s = run(true, step, 1000 / 60.0, 1200);
            double[] r = run(false, step, 1000 / 60.0, 1200);
            String what = "step " + step + " smooth sd " + s[1] + " raw sd " + r[1] + " min " + s[2] + " max " + s[3] + " err " + s[4];
            assertEquals(1.0, s[5], what);
            assertTrue(s[1] < 1.0, what);
            assertTrue(s[1] < r[1] / 5, what);
            assertTrue(s[2] >= 0.9 * 1000 / 60.0 - 1e-9 && s[3] <= 1.1 * 1000 / 60.0 + 1e-9, "slew-limited: " + what);
            assertTrue(s[4] < step + 20, "tracks the audio: " + what);
            assertEquals(1000 / 60.0, s[0], 0.2, what);
        }
    }

    @Test
    void monotonicThroughJitteryFramesAndBackwardReadings() {
        SongClock c = new SongClock(0, true);
        c.start(0, true);
        double prev = 0;
        double stamp = 0;
        long seed = 7;
        for (int i = 0; i < 2000; i++) {
            seed = seed * 6364136223846793005L + 1442695040888963407L;
            double frame = 8 + ((seed >>> 33) % 40);          // 8..47 ms frames, rAF delta spikes
            stamp += frame;
            double reading = Math.floor(stamp / 40) * 40 - ((seed >>> 20) % 3 == 0 ? 15 : 0); // coarse, sometimes behind
            double t = c.sample(stamp, true, reading);
            assertTrue(t >= prev, "monotonic at frame " + i);
            prev = t;
        }
        assertTrue(Math.abs(prev - stamp) < 120, "still on the audio: " + (prev - stamp));
    }

    @Test
    void holdsUntilTheAudioMovesThenCatchesUpSmoothly() {
        SmoothClock s = new SmoothClock();
        assertEquals(0.0, s.sample(0, 0), 0.0);
        for (int i = 1; i <= 20; i++) {
            assertEquals(0.0, s.sample(i * 16.0, 0), 0.0, "play() still starting: hold");
        }
        double prev = 0;
        for (int i = 21; i <= 200; i++) {
            double t = s.sample(i * 16.0, (i - 20) * 16.0);
            assertTrue(t - prev <= 1.1 * 16 + 1e-9 && t >= prev, "step " + (t - prev));
            prev = t;
        }
        assertEquals(180 * 16.0, prev, 3.0);
    }

    @Test
    void bigGapsSnapForwardAndHoldBehind() {
        SmoothClock s = new SmoothClock();
        s.sample(0, 1000);
        s.sample(16, 1016);
        assertEquals(5016.0, s.sample(32, 5016), 1e-9, "seek ahead: snap");
        double held = s.sample(48, 5032);
        double t = s.sample(64, 1000);                 // reading jumps back: hold, never backwards
        assertTrue(t >= held && t <= held + 1.1 * 16, "hold " + t);
        // stall: the reading stops; extrapolation is capped, so the estimate stops within MAX_EXTRAP + SNAP
        double last = 0;
        for (int i = 5; i < 200; i++) {
            last = s.sample(64 + i * 16.0, 5048);
        }
        assertTrue(last <= 5048 + SmoothClock.MAX_EXTRAP_MS + SmoothClock.SNAP_MS, "stall cap " + last);
    }

    @Test
    void pauseFreezesAndResumeReanchors() {
        SongClock c = new SongClock(0);
        c.start(1000, false);
        c.sample(4000, false, 0);
        assertEquals(3000.0, c.now(), 0.0);
        c.pause();
        assertTrue(c.isPaused());
        assertEquals(3000.0, c.sample(9000, false, 0), 0.0, "frozen while hidden");
        c.resume(14000);
        assertEquals(3000.0, c.sample(14000, false, 0), 0.0, "the hidden 10 s are not added");
        assertEquals(3016.0, c.sample(14016, false, 0), 0.0);
        // audio mode: song time follows the audio, which was paused alongside and resumes where it stopped
        SongClock a = new SongClock(0, true);
        a.start(0, true);
        a.sample(16, true, 0);
        a.sample(1500, true, 1500);
        double frozen = a.now();
        a.pause();
        assertEquals(frozen, a.sample(60000, true, 1500), 0.0);
        a.resume(60000);
        double back = a.sample(60000, true, 1500);
        assertTrue(back >= frozen && back <= 1500.0, "resumes at the paused audio position (no rewind, no 58 s jump): " + back);
        assertTrue(a.sample(60016, true, 1516) >= frozen);
        assertTrue(a.isAudioMode());
        // pause before start / resume without pause: no-ops
        SongClock idle = new SongClock(0);
        idle.pause();
        assertTrue(!idle.isPaused());
        idle.resume(5);
        assertEquals(0.0, idle.now(), 0.0);
    }
}
