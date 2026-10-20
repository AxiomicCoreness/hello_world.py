package com.fruitfly.games.rhythm.logic;

/**
 * Hit quality. Windows are symmetric (|press - note| &lt;= window). A note that
 * passes the GOOD window without a press becomes a MISS.
 */
public enum Judgement {
    PERFECT(50, 300),
    GREAT(100, 200),
    GOOD(150, 100),
    MISS(-1, 0);

    private final long windowMs;
    private final int baseScore;

    Judgement(long windowMs, int baseScore) {
        this.windowMs = windowMs;
        this.baseScore = baseScore;
    }

    public long windowMs() {
        return windowMs;
    }

    public int baseScore() {
        return baseScore;
    }

    /** Widest window in which a press can still hit a note. */
    public static final long MAX_WINDOW_MS = 150;

    /** Judge a press offset (press time - note time). Returns null if outside every window. */
    public static Judgement forOffset(long offsetMs) {
        long d = Math.abs(offsetMs);
        if (d <= PERFECT.windowMs) {
            return PERFECT;
        }
        if (d <= GREAT.windowMs) {
            return GREAT;
        }
        if (d <= GOOD.windowMs) {
            return GOOD;
        }
        return null;
    }
}
