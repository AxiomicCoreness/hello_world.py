package com.fruitfly.games.rhythm.logic;

/**
 * Song clock with an audio source and a frame-clock fallback. Pure logic: the
 * web layer passes in the frame timestamp and, when audio exists, the audio
 * element's position; tests do the same with plain numbers.
 *
 * <ul>
 *   <li>Audio mode: {@code song = audioPositionMs + offsetMs}, read fresh on
 *       every sample as a double. Nothing is accumulated from per-frame deltas,
 *       so rounding can't drift.</li>
 *   <li>Fallback (no audio, or audio failed/ended): song time follows the
 *       frame clock. With no audio at all this is exactly the original
 *       {@code stamp - startStamp}. If audio stops part-way, the frame clock
 *       continues from the last audio reading, so play carries on.</li>
 *   <li>Song time never goes backwards.</li>
 *   <li>Pause / resume (tab hidden): {@link #pause} freezes song time;
 *       {@link #resume} re-anchors the frame-clock fallback at the resume
 *       stamp, so the time the tab spent hidden is not added. In audio mode
 *       the audio element is paused alongside and resumes from where it
 *       stopped, so its position carries on from the frozen time.</li>
 * </ul>
 */
public final class SongClock {
    private final long offsetMs;
    private boolean started;
    private boolean audioMode;
    private double anchorSong;
    private double anchorStamp;
    private double now;
    private boolean paused;
    /** null = raw audio reads (the original behaviour); else the smoother for drawing / judging. */
    private final SmoothClock smooth;

    public SongClock(long offsetMs) {
        this(offsetMs, false);
    }

    /** @param smoothAudio steer a frame-clock estimate toward the audio ({@link SmoothClock}) instead of reading it raw. */
    public SongClock(long offsetMs, boolean smoothAudio) {
        this.offsetMs = offsetMs;
        this.smooth = smoothAudio ? new SmoothClock() : null;
    }

    public boolean isSmoothed() {
        return smooth != null;
    }

    /** Start a run at frame time {@code stampMs}; {@code withAudio} picks audio mode. */
    public void start(double stampMs, boolean withAudio) {
        started = true;
        audioMode = withAudio;
        anchorSong = 0.0;
        anchorStamp = stampMs;
        now = 0.0;
        paused = false;
        if (smooth != null) {
            smooth.reset();
        }
    }

    /** Freeze song time (no-op before start or when already paused). */
    public void pause() {
        if (started) {
            paused = true;
        }
    }

    /** Unfreeze at frame time {@code stampMs}: the fallback clock continues from the frozen time, not from the stamp gap. */
    public void resume(double stampMs) {
        if (!paused) {
            return;
        }
        paused = false;
        anchorSong = now;
        anchorStamp = stampMs;
        if (smooth != null) {
            smooth.reset(); // the paused audio resumes where it stopped: take its next reading as is
        }
    }

    public boolean isPaused() {
        return paused;
    }

    /** Back to the not-started state (song time 0). */
    public void stop() {
        started = false;
        audioMode = false;
        paused = false;
        now = 0.0;
    }

    /**
     * Current song time in ms.
     *
     * @param stampMs   frame clock (e.g. the requestAnimationFrame timestamp)
     * @param audioOk   whether the audio is still a valid clock (loaded, not failed, not ended)
     * @param audioPosMs the audio position in ms (ignored unless audioOk)
     */
    public double sample(double stampMs, boolean audioOk, double audioPosMs) {
        if (!started) {
            return 0.0;
        }
        if (paused) {
            return now;
        }
        double t;
        if (audioMode && audioOk) {
            t = smooth != null ? smooth.sample(stampMs, audioPosMs + offsetMs) : audioPosMs + offsetMs;
            anchorSong = Math.max(now, t);
            anchorStamp = stampMs;
        } else {
            if (audioMode) {
                // Audio just dropped out: keep going on the frame clock from the last reading.
                audioMode = false;
            }
            t = anchorSong + (stampMs - anchorStamp);
        }
        if (t > now) {
            now = t;
        }
        return now;
    }

    /** Last sampled song time in ms (0 before start). */
    public double now() {
        return now;
    }

    /** Song time as whole ms for {@link RhythmGame}: floor, so a note is never judged early. */
    public long nowMs() {
        return (long) Math.floor(now);
    }

    public boolean isAudioMode() {
        return started && audioMode;
    }

    public boolean isStarted() {
        return started;
    }

    public long offsetMs() {
        return offsetMs;
    }
}
