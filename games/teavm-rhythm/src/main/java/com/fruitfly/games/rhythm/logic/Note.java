package com.fruitfly.games.rhythm.logic;

/** One note: which lane it falls in and the time (ms from song start) it should be hit. */
public final class Note {
    private final int lane;
    private final long timeMs;
    private Judgement result;
    private long judgedAtMs = Long.MIN_VALUE;
    private int actor = ACTOR_NONE;

    /** Who judged the note: nobody (live or MISS), the human, or a fly brain's spike. */
    public static final int ACTOR_NONE = 0;
    public static final int ACTOR_HUMAN = 1;
    public static final int ACTOR_FLY = 2;

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
        resolve(j, Long.MIN_VALUE);
    }

    void resolve(Judgement j, long atMs) {
        resolve(j, atMs, ACTOR_NONE);
    }

    void resolve(Judgement j, long atMs, int by) {
        if (result != null) {
            throw new IllegalStateException("note already resolved");
        }
        result = j;
        judgedAtMs = atMs;
        actor = by;
    }

    /** {@link #ACTOR_NONE} for a MISS or a live note, else who pressed it. Display / moves list only. */
    public int actor() {
        return actor;
    }

    /** Song time of the press that judged this note (Long.MIN_VALUE for a MISS or while live). Display use only. */
    public long judgedAtMs() {
        return judgedAtMs;
    }
}
