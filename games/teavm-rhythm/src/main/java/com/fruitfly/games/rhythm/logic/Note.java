package com.fruitfly.games.rhythm.logic;

/** One note: which lane it falls in and the time (ms from song start) it should be hit. */
public final class Note {
    private final int lane;
    private final long timeMs;
    private Judgement result;

    public Note(int lane, long timeMs) {
        if (lane < 0 || lane >= RhythmGame.LANES) {
            throw new IllegalArgumentException("lane out of range: " + lane);
        }
        if (timeMs < 0) {
            throw new IllegalArgumentException("timeMs must be >= 0: " + timeMs);
        }
        this.lane = lane;
        this.timeMs = timeMs;
    }

    public int lane() {
        return lane;
    }

    public long timeMs() {
        return timeMs;
    }

    /** null while the note is still live; otherwise how it was judged (MISS included). */
    public Judgement result() {
        return result;
    }

    public boolean isResolved() {
        return result != null;
    }

    void resolve(Judgement j) {
        if (result != null) {
            throw new IllegalStateException("note already resolved");
        }
        result = j;
    }
}
