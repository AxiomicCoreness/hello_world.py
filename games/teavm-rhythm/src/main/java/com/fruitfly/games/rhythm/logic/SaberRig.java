package com.fruitfly.games.rhythm.logic;

/**
 * The toy fly's two sabers. Each saber PIVOTS about a fixed hand point and
 * never translates: its base is always the hand, its tip is the hand plus
 * LENGTH * dir(t). The direction is a pure function of song time and the
 * side's recorded swings.
 *
 * A swing is aimed at one lane's note block at the hit plane. Its plane
 * holds the aim vector a = normalise(blockAtHitPlane - hand) and p, the
 * world up made perpendicular to a. In that plane the blade direction is
 * cos(theta) a + sin(theta) p, so theta = 0 points the blade straight
 * through the block centre:
 *
 * <pre>
 *   0 .. LEAD             idle (or the previous swing's pose) -> raised (theta = RAISE), nlerp
 *   LEAD .. LEAD+STRIKE   constant-speed downward arc RAISE -> LOW, crossing theta = 0
 *                         (the block) at CONTACT_MS
 *   .. +RECOVER           LOW -> idle (smoothstep nlerp)
 * </pre>
 *
 * Swings start at the song time of each judged hit (Note.judgedAtMs), human
 * or fly: lanes 0-1 (D F) swing the left saber, lanes 2-3 (J K) the right.
 * Display only: the rhythm score never reads this.
 */
public final class SaberRig {
    public static final double LENGTH = 1.25;
    public static final double RADIUS = 0.045;
    /** Idle pose: angled outward by IDLE from vertical, leaning LEAN towards the horizon (-z). */
    public static final double IDLE = Math.toRadians(62);
    public static final double LEAN = Math.toRadians(32);
    /** Swing plane angles: raised above the block, then down through it to LOW. */
    public static final double RAISE = Math.toRadians(70);
    public static final double LOW = Math.toRadians(-50);
    public static final double LEAD_MS = 12;
    public static final double STRIKE_MS = 50;
    public static final double RECOVER_MS = 220;
    public static final double SWING_TOTAL_MS = LEAD_MS + STRIKE_MS + RECOVER_MS;
    /** ms after the swing starts when the blade passes through the block centre (theta = 0). */
    public static final double CONTACT_MS = LEAD_MS + STRIKE_MS * RAISE / (RAISE - LOW);
    /** Hands, world units: left (side 0) and right (side 1). The fly stands on the centre tile at the origin. */
    public static final double[][] HANDS = {{-0.34, 0.62, -0.1}, {0.34, 0.62, -0.1}};
    private static final double[] UP = {0, 1, 0};
    private static final int MAX_DEPTH = 8;

    private final long[][] starts = new long[2][];
    private final int[][] lanes = new int[2][];
    private final int[] counts = new int[2];
    private boolean[] seenFlags = new boolean[0];

    public SaberRig() {
        for (int s = 0; s < 2; s++) {
            starts[s] = new long[16];
            lanes[s] = new int[16];
        }
    }

    /** Side index 0 = left, 1 = right, for a lane. */
    public static int sideFor(int lane) {
        return lane < 2 ? 0 : 1;
    }

    /** Record a swing for every newly judged hit in the chart (call each frame; idempotent). MISSes never swing. */
    public void sync(NoteChart chart) {
        java.util.List<Note> notes = chart.notes();
        if (seenFlags.length < notes.size()) {
            seenFlags = java.util.Arrays.copyOf(seenFlags, notes.size());
        }
        for (int i = 0; i < notes.size(); i++) {
            Note n = notes.get(i);
            if (!seenFlags[i] && NoteBlocks.isHit(n)) {
                seenFlags[i] = true;
                trigger(n.lane(), n.judgedAtMs());
            }
        }
    }

    /** Start a swing aimed at {@code lane}'s block, at song time {@code atMs}. */
    public void trigger(int lane, long atMs) {
        int side = sideFor(lane);
        if (counts[side] == starts[side].length) {
            starts[side] = java.util.Arrays.copyOf(starts[side], counts[side] * 2);
            lanes[side] = java.util.Arrays.copyOf(lanes[side], counts[side] * 2);
        }
        starts[side][counts[side]] = atMs;
        lanes[side][counts[side]] = lane;
        counts[side]++;
    }

    public int swingCount(int side) {
        return counts[side];
    }

    // ---- pure swing geometry ----

    /** Unit aim vector from the lane's hand to the lane's block centre at the hit plane. */
    public static double[] aim(int lane) {
        return StageGeometry.normalize(StageGeometry.sub(NoteBlocks.hitCentre(lane), HANDS[sideFor(lane)]));
    }

    /** Unit in-plane "up" of the lane's swing plane (world up minus its component along the aim). */
    public static double[] planeUp(int lane) {
        double[] a = aim(lane);
        double k = StageGeometry.dot(UP, a);
        return StageGeometry.normalize(new double[] {UP[0] - k * a[0], UP[1] - k * a[1], UP[2] - k * a[2]});
    }

    /** Normal of the lane's swing plane: the cut plane splits the block along this axis. */
    public static double[] cutNormal(int lane) {
        return StageGeometry.normalize(StageGeometry.cross(aim(lane), planeUp(lane)));
    }

    /** Blade direction in the lane's swing plane at angle theta (0 = through the block centre). */
    public static double[] arcDirection(int lane, double theta) {
        double[] a = aim(lane);
        double[] p = planeUp(lane);
        double c = Math.cos(theta);
        double s = Math.sin(theta);
        return new double[] {c * a[0] + s * p[0], c * a[1] + s * p[1], c * a[2] + s * p[2]};
    }

    /** Idle blade direction: outward (side sign) by IDLE from vertical, leaning towards the horizon. */
    public static double[] idleDirection(int side) {
        double sign = side == 0 ? -1 : 1;
        double cl = Math.cos(LEAN);
        return new double[] {sign * Math.sin(IDLE) * cl, Math.cos(IDLE) * cl, -Math.sin(LEAN)};
    }

    /** Swing-plane angle during the strike phase, for ms since the swing started (clamped to the phase). */
    public static double strikeAngle(double sinceMs) {
        double u = Math.max(0, Math.min(1, (sinceMs - LEAD_MS) / STRIKE_MS));
        return RAISE + (LOW - RAISE) * u;
    }

    private static double[] nlerp(double[] a, double[] b, double u) {
        double[] m = {a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u};
        return StageGeometry.normalize(m);
    }

    private static double smooth(double u) {
        return u * u * (3 - 2 * u);
    }

    /** Index of the latest swing with start &lt;= t and start &lt; bound (later-recorded wins ties), or -1. */
    private int latest(int side, double t, double bound) {
        int best = -1;
        for (int i = 0; i < counts[side]; i++) {
            long s = starts[side][i];
            if (s <= t && s < bound && (best < 0 || s >= starts[side][best])) {
                best = i;
            }
        }
        return best;
    }

    /** Unit blade direction of {@code side} at song time t. */
    public double[] direction(int side, double t) {
        return direction(side, t, Double.POSITIVE_INFINITY, 0);
    }

    private double[] direction(int side, double t, double bound, int depth) {
        int k = depth >= MAX_DEPTH ? -1 : latest(side, t, bound);
        if (k < 0) {
            return idleDirection(side);
        }
        double s = starts[side][k];
        double since = t - s;
        int lane = lanes[side][k];
        if (since >= SWING_TOTAL_MS) {
            return idleDirection(side);
        }
        if (since < LEAD_MS) {
            double[] from = direction(side, s, s, depth + 1); // pose just before this swing (continuous)
            return nlerp(from, arcDirection(lane, RAISE), smooth(since / LEAD_MS));
        }
        if (since < LEAD_MS + STRIKE_MS) {
            return arcDirection(lane, strikeAngle(since));
        }
        double u = (since - LEAD_MS - STRIKE_MS) / RECOVER_MS;
        return nlerp(arcDirection(lane, LOW), idleDirection(side), smooth(u));
    }

    /** True while a swing (lead, strike, recovery) is in progress on that side. */
    public boolean swinging(int side, double t) {
        int k = latest(side, t, Double.POSITIVE_INFINITY);
        return k >= 0 && t - starts[side][k] < SWING_TOTAL_MS;
    }

    /** {base, tip} of a saber at song time; base is always the hand. */
    public double[][] segment(int side, double t) {
        double[] h = HANDS[side];
        double[] d = direction(side, t);
        return new double[][] {h.clone(), {h[0] + LENGTH * d[0], h[1] + LENGTH * d[1], h[2] + LENGTH * d[2]}};
    }
}
