package com.fruitfly.games.rhythm.logic;

import java.util.List;
import java.util.function.LongConsumer;

/**
 * Assist mode: the human plays, the fly covers notes the human would miss.
 *
 * Every press, human or fly, goes through {@link RhythmGame#press}, so a note
 * is judged at most once and whoever presses first gets it.
 * <ul>
 *   <li>Human presses ({@link #human}) are always passed on. Before each one
 *       the brain is advanced to the press time, so presses reach the game in
 *       time order.</li>
 *   <li>The fly's brain is cued to spike {@link #FLY_AIM_MS} after each note
 *       (late in the 150 ms window). Its press ({@link #fly}) is passed on only
 *       if the note it would hit is still unresolved and already at least
 *       {@link #FLY_MIN_LATE_MS} late, i.e. the human hasn't hit it and it's
 *       about to become a MISS. Otherwise the press is held (dropped), so the
 *       fly can never take a note early or steal the next one in the lane.</li>
 * </ul>
 * Why 95 ms and not, say, 140: the brain runs in whole 50 ms ticks that end at
 * or before song time, so a spike at s is only simulated once song time
 * reaches the end of its tick (at most s + 50). Aiming at note + 95 keeps that
 * at or before note + 145, before the game's MISS cut-off at note + 150, at
 * any frame rate. A fly cover therefore scores GREAT (50 &lt; 95 &lt;= 100 ms).
 * Deterministic: no randomness, no wall clock.
 */
public final class AssistArbiter implements PressSink {
    public static final long FLY_AIM_MS = 95;
    public static final long FLY_MIN_LATE_MS = 75;

    private final RhythmGame game;
    private LongConsumer brain;
    private int humanHits;
    private int flyHits;
    private int flyHeld;

    public AssistArbiter(RhythmGame game) {
        this.game = game;
    }

    /** The brain's advanceTo, called before each human press. */
    public void attachBrain(LongConsumer advanceTo) {
        this.brain = advanceTo;
    }

    /** A human key press. Returns the judgement (null if nothing was hit). */
    public Judgement human(int lane, long timeMs) {
        if (brain != null) {
            brain.accept(timeMs);
        }
        Judgement j = game.press(lane, timeMs);
        if (j != null) {
            humanHits++;
        }
        return j;
    }

    /** A fly spike-press; passed on only to cover a note that is about to be missed. */
    public void fly(int lane, long timeMs) {
        Note n = noteFor(lane, timeMs);
        if (n == null || timeMs - n.timeMs() < FLY_MIN_LATE_MS) {
            flyHeld++;
            return;
        }
        if (game.press(lane, timeMs, true) != null) {
            flyHits++;
        } else {
            flyHeld++;
        }
    }

    @Override
    public void press(int lane, long timeMs) {
        fly(lane, timeMs);
    }

    /** The note RhythmGame.press(lane, t) would judge: earliest unresolved one in the lane within the window. */
    Note noteFor(int lane, long t) {
        List<Note> notes = game.chart().notes();
        for (Note n : notes) {
            if (n.timeMs() - t > Judgement.MAX_WINDOW_MS) {
                break;
            }
            if (!n.isResolved() && n.lane() == lane && Judgement.forOffset(t - n.timeMs()) != null) {
                return n;
            }
        }
        return null;
    }

    public int humanHits() {
        return humanHits;
    }

    public int flyHits() {
        return flyHits;
    }

    /** Fly presses dropped because the human already had the note (or none was due). */
    public int flyHeld() {
        return flyHeld;
    }
}
