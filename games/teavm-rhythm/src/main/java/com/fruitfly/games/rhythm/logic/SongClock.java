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
 * </ul>
 */
public final class SongClock {
    private final long offsetMs;
    private boolean started;
    private boolean audioMode;
    private double anchorSong;
    private double anchorStamp;
    private double now;

    public SongClock(long offsetMs) {
        this.offsetMs = offsetMs;
    }

    /** Start a run at frame time {@code stampMs}; {@code withAudio} picks audio mode. */
    public void start(double stampMs, boolean withAudio) {
        started = true;
        audioMode = withAudio;
        anchorSong = 0.0;
        anchorStamp = stampMs;
        now = 0.0;
    }

    /** Back to the not-started state (song time 0). */
    public void stop() {
        started = false;
        audioMode = false;
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
        double t;
        if (audioMode && audioOk) {
            t = audioPosMs + offsetMs;
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
