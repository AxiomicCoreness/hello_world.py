package com.fruitfly.games.rhythm.logic;

/**
 * The chart notes as 3D blocks (Beat-Saber style). Pure functions of a note
 * and song time t; display only (RhythmGame alone scores).
 *
 * Each note's block rides its lane's line on the floor: it appears at
 * z = Z_SPAWN, far down the lane next to the vanishing point, APPROACH_MS before
 * the note's time, and travels towards the player at constant speed, so
 *
 * <pre>
 *   z(t) = Z_HIT + (t - time_ms) * SPEED,   SPEED = (Z_HIT - Z_SPAWN) / APPROACH_MS
 * </pre>
 *
 * and it is exactly on the hit plane z = Z_HIT (just in front of the fly's
 * sabers) at t = time_ms. Lane x positions spread D F J K left to right.
 *
 * States:
 *  - APPROACH: on its way (fades in over FADE_IN_MS).
 *  - HELD: judged hit (human or fly): the block is held at the hit plane
 *    from the press until the saber blade reaches it (SaberRig.CONTACT_MS).
 *  - SLICED: from contact, two halves split apart along the swing plane's
 *    normal, flash, drift and fade over SLICE_MS.
 *  - PASSED: not (yet) hit after time_ms, or MISSed: it keeps going past the
 *    hit plane and fades out over PASS_FADE_MS.
 * Blocks cut at t = judged hits whose contact time has passed, so after a
 * song the count equals RhythmGame's hit count.
 */
public final class NoteBlocks {
    public static final double[] LANE_X = {-0.9, -0.3, 0.3, 0.9};
    public static final double LANE_WIDTH = 0.6;
    public static final double SIZE = 0.4;
    /** Block centre height (the sabers' hand height). */
    public static final double Y = 0.62;
    public static final double Z_HIT = -0.8;
    public static final double Z_SPAWN = -40.0;
    public static final double APPROACH_MS = 2000.0;
    public static final double SPEED = (Z_HIT - Z_SPAWN) / APPROACH_MS;
    public static final double FADE_IN_MS = 250;
    public static final double PASS_FADE_MS = 350;
    public static final double SLICE_MS = 420;
    public static final double FLASH_MS = 110;
    /** Sliced halves: extra gap along the cut normal and outward tilt reached at the end of SLICE_MS. */
    public static final double SPLIT = 0.28;
    public static final double TILT = Math.toRadians(35);

    public static final int HIDDEN = 0;
    public static final int APPROACH = 1;
    public static final int HELD = 2;
    public static final int SLICED = 3;
    public static final int PASSED = 4;

    private NoteBlocks() {
    }

    /** Judged as a hit (PERFECT/GREAT/GOOD) with a known press time. */
    public static boolean isHit(Note n) {
        return n.isResolved() && n.result() != Judgement.MISS && n.judgedAtMs() != Long.MIN_VALUE;
    }

    /** z of a block on its approach path at song time t (no clamping). */
    public static double z(long noteMs, double t) {
        return Z_HIT + (t - noteMs) * SPEED;
    }

    public static double[] hitCentre(int lane) {
        return new double[] {LANE_X[lane], Y, Z_HIT};
    }

    /** Centre on the approach path at song time t. */
    public static double[] pathCentre(int lane, long noteMs, double t) {
        return new double[] {LANE_X[lane], Y, z(noteMs, t)};
    }

    /** Song time the blade reaches a hit note's block, or NaN for a live / missed note. */
    public static double contactMs(Note n) {
        return isHit(n) ? n.judgedAtMs() + SaberRig.CONTACT_MS : Double.NaN;
    }

    public static int state(Note n, double t) {
        long nt = n.timeMs();
        if (t < nt - APPROACH_MS) {
            return HIDDEN;
        }
        if (isHit(n) && t >= n.judgedAtMs()) {
            double c = contactMs(n);
            if (t < c) {
                return HELD;
            }
            return t < c + SLICE_MS ? SLICED : HIDDEN;
        }
        if (t <= nt) {
            return APPROACH;
        }
        return t < nt + PASS_FADE_MS ? PASSED : HIDDEN;
    }

    /** Centre of the (whole) block for APPROACH / HELD / PASSED; the hit plane for SLICED. */
    public static double[] centre(Note n, double t) {
        int s = state(n, t);
        if (s == HELD || s == SLICED) {
            return hitCentre(n.lane());
        }
        return pathCentre(n.lane(), n.timeMs(), t);
    }

    /** Opacity 0..1 for a state at song time t. */
    public static double alpha(Note n, double t) {
        switch (state(n, t)) {
            case APPROACH:
                return Math.min(1, (t - (n.timeMs() - APPROACH_MS)) / FADE_IN_MS);
            case HELD:
                return 1;
            case SLICED:
                return 1 - (t - contactMs(n)) / SLICE_MS;
            case PASSED:
                return 1 - (t - n.timeMs()) / PASS_FADE_MS;
            default:
                return 0;
        }
    }

    /** Whole-block corners (axis-aligned cube). */
    public static double[][] corners(Note n, double t) {
        return StageGeometry.cube(centre(n, t), SIZE);
    }

    /**
     * The two halves of a sliced block, {@code sinceContactMs} after contact:
     * each is a SIZE/2-thick slab on one side of the cut plane (through the
     * block centre, normal SaberRig.cutNormal), moving apart along the
     * normal, dropping a little and drifting on towards the player.
     */
    public static double[][][] halves(int lane, double sinceContactMs) {
        double u = Math.max(0, Math.min(1, sinceContactMs / SLICE_MS));
        double[] n = SaberRig.cutNormal(lane);
        double k = n[1];
        double[] b = StageGeometry.normalize(new double[] {-k * n[0], 1 - k * n[1], -k * n[2]});
        double[] c = StageGeometry.cross(n, b);
        double[] h = hitCentre(lane);
        double[][][] out = new double[2][][];
        for (int side = 0; side < 2; side++) {
            double sg = side == 0 ? -1 : 1;
            double off = SIZE / 4 + SPLIT * u;
            // Each half tilts away from the cut about the forward axis c (top falls outward).
            double a = sg * TILT * u;
            double ca = Math.cos(a);
            double sa = Math.sin(a);
            double[] n2 = {ca * n[0] + sa * b[0], ca * n[1] + sa * b[1], ca * n[2] + sa * b[2]};
            double[] b2 = {-sa * n[0] + ca * b[0], -sa * n[1] + ca * b[1], -sa * n[2] + ca * b[2]};
            double[] ctr = {
                h[0] + sg * n[0] * off,
                h[1] + sg * n[1] * off - 0.35 * u * u,
                h[2] + sg * n[2] * off + 0.15 * SPEED * sinceContactMs,
            };
            out[side] = StageGeometry.box(ctr, n2, b2, c, SIZE / 4, SIZE / 2, SIZE / 2);
        }
        return out;
    }

    /**
     * The HUD's "blocks cut": judged hits pressed at or before song time t.
     * It moves on the same press as RhythmGame's score / combo / hit count,
     * so the counters never disagree. The block's split animation starts
     * later, at blade contact ({@link #cutCount}).
     */
    public static int hitCount(NoteChart chart, double t) {
        int c = 0;
        for (Note n : chart.notes()) {
            if (isHit(n) && n.judgedAtMs() <= t) {
                c++;
            }
        }
        return c;
    }

    /** Blocks visibly split by song time t: judged hits whose blade contact has happened (animation only). */
    public static int cutCount(NoteChart chart, double t) {
        int c = 0;
        for (Note n : chart.notes()) {
            if (isHit(n) && contactMs(n) <= t) {
                c++;
            }
        }
        return c;
    }

    /** Latest blade contact at or before t, or -infinity. */
    public static double lastCutAt(NoteChart chart, double t) {
        double best = Double.NEGATIVE_INFINITY;
        for (Note n : chart.notes()) {
            double c = contactMs(n);
            if (c <= t && c > best) {
                best = c;
            }
        }
        return best;
    }
}
