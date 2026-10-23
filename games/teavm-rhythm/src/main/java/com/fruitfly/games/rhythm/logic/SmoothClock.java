package com.fruitfly.games.rhythm.logic;

/**
 * Smooths a coarse audio clock for drawing and judging.
 *
 * Why: a page reads {@code audio.currentTime} once per animation frame, but
 * browsers update it on their own timer. Safari (iOS in particular) moves it
 * in steps of tens of ms, so at 60 fps the raw reading stays put for one or
 * two frames and then jumps 30-50 ms: blocks placed from it stutter even
 * though nothing is lost on average.
 *
 * How: the estimate free-runs on the frame clock (est += frame delta) and is
 * steered toward the audio. The audio target is the last reading plus the
 * time since that reading last changed (capped at {@link #MAX_EXTRAP_MS}, so
 * a stalled element stops pulling the estimate forward; and no extrapolation
 * before the first change, while play() is still starting). Each frame
 * {@link #GAIN} of the error is corrected, limited to {@link #SLEW} x the frame delta, so the per-frame
 * step stays within 0.9x .. 1.1x of real time and never goes backwards.
 * A gap larger than {@link #SNAP_MS} (seek, start, long stall) is not slewed:
 * ahead -> jump to the audio; behind -> hold until the audio catches up.
 * Pure logic, deterministic: inputs are frame stamps and readings.
 */
public final class SmoothClock {
    public static final double SLEW = 0.1;
    /** Fraction of the remaining error corrected per frame (a low-pass on the coarse target). */
    public static final double GAIN = 0.08;
    public static final double SNAP_MS = 150;
    public static final double MAX_EXTRAP_MS = 300;

    private boolean init;
    private double est;
    private double lastStamp;
    private double lastReading;
    private double readingChangedAt;
    private boolean moving;

    /** Forget the history; the next sample takes the reading as is. */
    public void reset() {
        init = false;
    }

    /** Estimate at frame time {@code stampMs} given the raw reading {@code readingMs}. */
    public double sample(double stampMs, double readingMs) {
        if (!init) {
            init = true;
            est = readingMs;
            lastStamp = stampMs;
            lastReading = readingMs;
            readingChangedAt = stampMs;
            moving = false;
            return est;
        }
        double ds = Math.max(0.0, stampMs - lastStamp);
        lastStamp = Math.max(lastStamp, stampMs);
        if (readingMs != lastReading) {
            lastReading = readingMs;
            readingChangedAt = lastStamp;
            moving = true;
        }
        // No extrapolation until the audio has moved once (play() still starting up).
        double target = lastReading + (moving ? Math.min(MAX_EXTRAP_MS, lastStamp - readingChangedAt) : 0.0);
        if (!moving) {
            est = Math.max(est, target); // hold on the first reading until the audio actually moves
            return est;
        }
        double pred = est + ds;
        double e = target - pred;
        if (e > SNAP_MS) {
            est = target;
        } else if (e < -SNAP_MS) {
            est = Math.max(est, target); // audio is behind (stall / seek back): hold
        } else {
            double lim = SLEW * ds;
            est = pred + Math.max(-lim, Math.min(lim, GAIN * e));
        }
        return est;
    }
}
