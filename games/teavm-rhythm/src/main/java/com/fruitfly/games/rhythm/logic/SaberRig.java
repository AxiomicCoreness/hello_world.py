package com.fruitfly.games.rhythm.logic;

/**
 * The toy fly's two sabers. Each saber PIVOTS about a fixed hand point and
 * never translates: its base is always the hand, its tip is the hand plus
 * LENGTH * dir(theta). The angle is a pure function of song time and the
 * side's last swing start:
 *
 * <pre>
 *   idle        theta = IDLE (angled outward)
 *   0..SWING    fast inward arc IDLE -> STRIKE (ease-out)
 *   ..+RECOVER  recovery STRIKE -> IDLE (smoothstep)
 * </pre>
 *
 * A swing starts at the song time of each judged hit (Note.judgedAtMs):
 * lanes 0-1 swing the left saber, lanes 2-3 the right. Display only.
 */
public final class SaberRig {
    public static final double LENGTH = 1.25;
    public static final double RADIUS = 0.045;
    public static final double IDLE = Math.toRadians(62);
    public static final double STRIKE = Math.toRadians(-48);
    public static final double SWING_MS = 90;
    public static final double RECOVER_MS = 260;
    /** Forward lean (towards -z, where the blocks come from), radians. */
    public static final double LEAN = Math.toRadians(32);
    /** Hands, world units: left (side -1) and right (side +1). The fly stands on the tile at the origin. */
    public static final double[][] HANDS = {{-0.34, 0.58, 0.12}, {0.34, 0.58, 0.12}};

    private final long[][] swings = new long[2][];
    private final int[] counts = new int[2];

    public SaberRig() {
        swings[0] = new long[16];
        swings[1] = new long[16];
    }

    /** Side index 0 = left, 1 = right, for a lane. */
    public static int sideFor(int lane) {
        return lane < 2 ? 0 : 1;
    }

    /** Record swings for every newly judged hit in the chart (call each frame; idempotent). */
    public void sync(NoteChart chart) {
        java.util.List<Note> notes = chart.notes();
        for (int i = 0; i < notes.size(); i++) {
            Note n = notes.get(i);
            if (n.isResolved() && n.result() != Judgement.MISS && n.judgedAtMs() != Long.MIN_VALUE && !seen(i)) {
                markSeen(i, notes.size());
                trigger(sideFor(n.lane()), n.judgedAtMs());
            }
        }
    }

    private boolean[] seenFlags = new boolean[0];

    private boolean seen(int i) {
        return i < seenFlags.length && seenFlags[i];
    }

    private void markSeen(int i, int n) {
        if (seenFlags.length < n) {
            seenFlags = java.util.Arrays.copyOf(seenFlags, n);
        }
        seenFlags[i] = true;
    }

    /** Start a swing of {@code side} at song time {@code atMs}. */
    public void trigger(int side, long atMs) {
        if (counts[side] == swings[side].length) {
            swings[side] = java.util.Arrays.copyOf(swings[side], counts[side] * 2);
        }
        swings[side][counts[side]++] = atMs;
    }

    public int swingCount(int side) {
        return counts[side];
    }

    /** Latest swing start at or before t, or Long.MIN_VALUE (order of triggers doesn't matter). */
    private long lastSwing(int side, double t) {
        long best = Long.MIN_VALUE;
        for (int i = 0; i < counts[side]; i++) {
            if (swings[side][i] <= t && swings[side][i] > best) {
                best = swings[side][i];
            }
        }
        return best;
    }

    /** Pure angle profile for ms since the swing started (any value outside the swing is idle). */
    public static double angleAt(double sinceMs) {
        if (!(sinceMs >= 0) || sinceMs >= SWING_MS + RECOVER_MS) {
            return IDLE;
        }
        if (sinceMs < SWING_MS) {
            double u = sinceMs / SWING_MS;
            double e = 1 - (1 - u) * (1 - u);
            return IDLE + (STRIKE - IDLE) * e;
        }
        double u = (sinceMs - SWING_MS) / RECOVER_MS;
        double e = u * u * (3 - 2 * u);
        return STRIKE + (IDLE - STRIKE) * e;
    }

    /** True while a swing (arc + recovery) is in progress on that side. */
    public boolean swinging(int side, double songMs) {
        long s = lastSwing(side, songMs);
        return s != Long.MIN_VALUE && songMs - s < SWING_MS + RECOVER_MS;
    }

    public double angle(int side, double songMs) {
        long s = lastSwing(side, songMs);
        return s == Long.MIN_VALUE ? IDLE : angleAt(songMs - s);
    }

    /** Unit direction of a saber for an angle: outward (side sign) by theta from vertical, leaning forward. */
    public static double[] direction(int side, double theta) {
        double sign = side == 0 ? -1 : 1;
        double cl = Math.cos(LEAN);
        return new double[] {sign * Math.sin(theta) * cl, Math.cos(theta) * cl, -Math.sin(LEAN)};
    }

    /** {base, tip} of a saber at song time; base is always the hand. */
    public double[][] segment(int side, double songMs) {
        double[] h = HANDS[side];
        double[] d = direction(side, angle(side, songMs));
        return new double[][] {h.clone(), {h[0] + LENGTH * d[0], h[1] + LENGTH * d[1], h[2] + LENGTH * d[2]}};
    }
}
