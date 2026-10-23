package com.fruitfly.games.rhythm.logic;

import java.util.List;

/**
 * Pure game state: no browser, TeaVM or JSO types. The web layer feeds it
 * key presses and the current song time; tests drive it the same way.
 *
 * Rules:
 *  - press(lane, t) hits the earliest unresolved note in that lane whose
 *    |t - noteTime| is within the GOOD window; a press with no note in range
 *    is ignored (no penalty, no combo change).
 *  - update(t) turns every note with t - noteTime &gt; GOOD window into a MISS.
 *  - A hit adds baseScore * multiplier, where multiplier = min(4, 1 + combo/10)
 *    using the combo before this hit; then combo += 1. A MISS resets combo to 0.
 */
public final class RhythmGame {
    public static final int LANES = 4;
    /** Key per lane, left to right. */
    public static final String[] LANE_KEYS = {"D", "F", "J", "K"};
    public static final int MAX_MULTIPLIER = 4;

    private final NoteChart chart;
    private long score;
    private int combo;
    private int maxCombo;
    private int perfect;
    private int great;
    private int good;
    private int miss;
    private int nextUnresolved;
    private Judgement lastJudgement;

    public RhythmGame(NoteChart chart) {
        this.chart = chart;
    }

    /** Map a key (e.g. "d", "KeyD", "D") to a lane, or -1. */
    public static int laneForKey(String key) {
        if (key == null) {
            return -1;
        }
        String k = key.startsWith("Key") && key.length() == 4 ? key.substring(3) : key;
        if (k.length() != 1) {
            return -1;
        }
        String up = k.toUpperCase();
        for (int i = 0; i < LANE_KEYS.length; i++) {
            if (LANE_KEYS[i].equals(up)) {
                return i;
            }
        }
        return -1;
    }

    public static int multiplierFor(int combo) {
        return Math.min(MAX_MULTIPLIER, 1 + combo / 10);
    }

    /** Handle a key press in {@code lane} at song time {@code nowMs}. Returns the judgement, or null if nothing was hit. */
    public Judgement press(int lane, long nowMs) {
        return press(lane, nowMs, false);
    }

    /** As {@link #press(int, long)}; {@code byFly} records a fly brain's spike as the actor (moves list). */
    public Judgement press(int lane, long nowMs, boolean byFly) {
        if (lane < 0 || lane >= LANES) {
            return null;
        }
        update(nowMs);
        List<Note> notes = chart.notes();
        for (int i = nextUnresolved; i < notes.size(); i++) {
            Note n = notes.get(i);
            if (n.timeMs() - nowMs > Judgement.MAX_WINDOW_MS) {
                break; // sorted by time; later notes are further away
            }
            if (n.isResolved() || n.lane() != lane) {
                continue;
            }
            Judgement j = Judgement.forOffset(nowMs - n.timeMs());
            if (j == null) {
                continue;
            }
            n.resolve(j, nowMs, byFly ? Note.ACTOR_FLY : Note.ACTOR_HUMAN);
            score += (long) j.baseScore() * multiplierFor(combo);
            combo++;
            maxCombo = Math.max(maxCombo, combo);
            count(j);
            lastJudgement = j;
            advance();
            return j;
        }
        return null;
    }

    /** Advance song time: any note now past the GOOD window becomes a MISS. */
    public void update(long nowMs) {
        List<Note> notes = chart.notes();
        for (int i = nextUnresolved; i < notes.size(); i++) {
            Note n = notes.get(i);
            if (nowMs - n.timeMs() <= Judgement.MAX_WINDOW_MS) {
                break;
            }
            if (!n.isResolved()) {
                n.resolve(Judgement.MISS);
                combo = 0;
                miss++;
                lastJudgement = Judgement.MISS;
            }
        }
        advance();
    }

    private void advance() {
        List<Note> notes = chart.notes();
        while (nextUnresolved < notes.size() && notes.get(nextUnresolved).isResolved()) {
            nextUnresolved++;
        }
    }

    private void count(Judgement j) {
        switch (j) {
            case PERFECT:
                perfect++;
                break;
            case GREAT:
                great++;
                break;
            case GOOD:
                good++;
                break;
            default:
                miss++;
        }
    }

    public boolean isFinished() {
        return nextUnresolved >= chart.notes().size();
    }

    /** Hit accuracy in [0,1]: (300*P + 200*Gr + 100*Go) / (300 * judged). 1.0 before any note is judged. */
    public double accuracy() {
        int judged = perfect + great + good + miss;
        if (judged == 0) {
            return 1.0;
        }
        return (300.0 * perfect + 200.0 * great + 100.0 * good) / (300.0 * judged);
    }

    public NoteChart chart() {
        return chart;
    }

    public long score() {
        return score;
    }

    public int combo() {
        return combo;
    }

    public int maxCombo() {
        return maxCombo;
    }

    public int perfectCount() {
        return perfect;
    }

    public int greatCount() {
        return great;
    }

    public int goodCount() {
        return good;
    }

    public int missCount() {
        return miss;
    }

    public Judgement lastJudgement() {
        return lastJudgement;
    }
}
