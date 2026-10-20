package com.fruitfly.games.rhythm.logic;

import java.util.Arrays;

/**
 * Phantom blocks: translucent cubes that drift from the far, high part of
 * the scene down onto the centre floor tile (|x|, |z| &lt;= 1 at y = 0), sink
 * into it and respawn. DISPLAY ONLY: no effect on the rhythm game or score.
 *
 * Time base: SONG TIME. Every path is a pure function of song time and the
 * block's current cycle start, so the scene is deterministic and stands
 * still on the title screen (song time frozen at 0).
 *
 * The fly's sabers ({@link SaberRig}) cut blocks: while a saber is swinging,
 * {@link #advance} sub-steps song time on a global {@link #SUBSTEP_MS} ms grid and tests
 * the saber capsule against each cube in 3D (StageGeometry.capsuleHitsCube),
 * so a far block that merely overlaps the saber on screen is not hit. A cut
 * block flashes and expands/fades for {@link #FX_MS} ms, then respawns. A
 * block that reaches the tile just sinks in and respawns: no penalty.
 */
public final class PhantomBlocks {
    public static final int COUNT = 7;
    public static final double TILE_HALF = 1.0;
    public static final double FX_MS = 260;
    public static final double SUBSTEP_MS = 2;
    /** Fraction of a cycle spent flying; the rest is sinking into the tile. */
    public static final double LAND_U = 0.86;

    private final long seed;
    private final double[] cycleStart = new double[COUNT];
    private final int[] cycle = new int[COUNT];
    private final double[] hitAt = new double[COUNT];
    private final double[][] hitPos = new double[COUNT][];
    private final double[] hitSize = new double[COUNT];
    private final double[] hitYaw = new double[COUNT];
    private double lastT = Double.NaN;
    private int destroyed;
    private double lastCut = Double.NEGATIVE_INFINITY;
    private int landed;

    public PhantomBlocks(long seed) {
        this.seed = seed;
        reset();
    }

    private void reset() {
        for (int i = 0; i < COUNT; i++) {
            cycle[i] = 0;
            cycleStart[i] = -hash01(i, 0, 9) * period(i, 0); // staggered so they don't fall together
            hitAt[i] = Double.NaN;
        }
        lastT = Double.NaN;
        destroyed = 0;
        landed = 0;
        lastCut = Double.NEGATIVE_INFINITY;
    }

    // ---- deterministic per-(block, cycle) parameters ----

    static double hash01(int i, int c, int k) {
        long z = 0x9E3779B97F4A7C15L * (1 + i) + 0xBF58476D1CE4E5B9L * (1 + c) + 0x94D049BB133111EBL * (1 + k);
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        z ^= z >>> 31;
        return (z >>> 11) * 0x1.0p-53;
    }

    private double h(int i, int c, int k) {
        return hash01(i, c + (int) (seed * 31), k);
    }

    public double period(int i, int c) {
        return 6000 + 4000 * h(i, c, 1);
    }

    public double size(int i, int c) {
        return 0.2 + 0.14 * h(i, c, 2);
    }

    public double[] spawn(int i, int c) {
        return new double[] {-3 + 6 * h(i, c, 3), 3.2 + 1.8 * h(i, c, 4), -9 + 6 * h(i, c, 5)};
    }

    /** Landing point on the tile, kept inside it with room for the cube. */
    public double[] land(int i, int c) {
        double r = TILE_HALF - 0.4;
        return new double[] {-r + 2 * r * h(i, c, 6), 0.0, -r + 2 * r * h(i, c, 7)};
    }

    private double spin(int i, int c) {
        return (h(i, c, 8) - 0.5) * 3.0 * Math.PI;
    }

    /**
     * Pure path for cycle phase u in [0, 1): {cx, cy, cz, yaw, alpha}. Flight
     * (u &lt; LAND_U) eases from spawn to resting on the tile (y = size/2);
     * then it sinks through the tile and fades.
     */
    public double[] path(int i, int c, double u) {
        double[] a = spawn(i, c);
        double[] b = land(i, c);
        double sz = size(i, c);
        double yaw = spin(i, c) * u;
        if (u < LAND_U) {
            double s = u / LAND_U;
            double e = s * s * (3 - 2 * s);
            double sway = 0.25 * Math.sin(2 * Math.PI * 1.5 * s) * (1 - s);
            double y = a[1] + (sz / 2 - a[1]) * Math.pow(s, 1.5);
            double alpha = Math.min(1.0, u / 0.05);
            return new double[] {a[0] + (b[0] - a[0]) * e + sway, y, a[2] + (b[2] - a[2]) * e, yaw, alpha};
        }
        double k = (u - LAND_U) / (1 - LAND_U);
        return new double[] {b[0], sz / 2 - sz * k, b[2], yaw, 1 - k};
    }

    /** Is a saber capsule touching a cube? (3D test, not a screen-space one.) */
    public static boolean saberHits(double[][] saber, double[] centre, double size, double yaw) {
        return StageGeometry.capsuleHitsCube(saber[0], saber[1], SaberRig.RADIUS, centre, size, yaw);
    }

    /** Advance the field to song time t, settling landings/respawns and testing swinging sabers (rig may be null). */
    public void advance(double t, SaberRig rig) {
        if (Double.isNaN(lastT) || t < lastT) {
            if (!Double.isNaN(lastT)) {
                reset(); // restart / rewind: the scene is a function of song time again
            }
            lastT = t;
            settle(t);
            return;
        }
        // Sub-steps on a global 2 ms song-time grid, so cuts don't depend on frame timing.
        for (double tau = (Math.floor(lastT / SUBSTEP_MS) + 1) * SUBSTEP_MS; tau <= t; tau += SUBSTEP_MS) {
            settle(tau);
            if (rig != null) {
                cut(tau, rig);
            }
        }
        settle(t);
        lastT = t;
    }

    private void settle(double t) {
        for (int i = 0; i < COUNT; i++) {
            if (!Double.isNaN(hitAt[i])) {
                if (t >= hitAt[i] + FX_MS) {
                    cycleStart[i] = hitAt[i] + FX_MS;
                    cycle[i]++;
                    hitAt[i] = Double.NaN;
                } else {
                    continue;
                }
            }
            while (t - cycleStart[i] >= period(i, cycle[i])) {
                cycleStart[i] += period(i, cycle[i]);
                cycle[i]++;
                landed++;
            }
        }
    }

    private void cut(double t, SaberRig rig) {
        for (int side = 0; side < 2; side++) {
            if (!rig.swinging(side, t)) {
                continue;
            }
            double[][] seg = rig.segment(side, t);
            for (int i = 0; i < COUNT; i++) {
                if (!Double.isNaN(hitAt[i])) {
                    continue;
                }
                double u = (t - cycleStart[i]) / period(i, cycle[i]);
                double[] p = path(i, cycle[i], u);
                double sz = size(i, cycle[i]);
                if (saberHits(seg, p, sz, p[3])) {
                    hitAt[i] = t;
                    hitPos[i] = new double[] {p[0], p[1], p[2]};
                    hitSize[i] = sz;
                    hitYaw[i] = p[3];
                    destroyed++;
                    lastCut = t;
                }
            }
        }
    }

    /**
     * Block i at song time t (after advance(t)): {cx, cy, cz, size, yaw,
     * alpha, fx} where fx is -1 normally, else 0..1 through the cut effect
     * (flash, then expand and fade).
     */
    public double[] view(int i, double t) {
        if (!Double.isNaN(hitAt[i]) && t >= hitAt[i]) {
            double k = Math.min(1.0, (t - hitAt[i]) / FX_MS);
            double[] p = hitPos[i];
            return new double[] {p[0], p[1], p[2], hitSize[i] * (1 + 0.9 * k), hitYaw[i], 1 - k, k};
        }
        double u = Math.max(0, (t - cycleStart[i]) / period(i, cycle[i]));
        double[] p = path(i, cycle[i], Math.min(u, 0.999999));
        return new double[] {p[0], p[1], p[2], size(i, cycle[i]), p[3], p[4], -1};
    }

    /** Indices far-to-near by camera depth of the centre (painter's order). */
    public int[] depthOrder(Scene3D cam, double t) {
        Integer[] idx = new Integer[COUNT];
        double[] depth = new double[COUNT];
        for (int i = 0; i < COUNT; i++) {
            idx[i] = i;
            double[] v = view(i, t);
            depth[i] = cam.toCamera(v[0], v[1], v[2])[2];
        }
        Arrays.sort(idx, (a, b) -> Double.compare(depth[b], depth[a]));
        int[] out = new int[COUNT];
        for (int i = 0; i < COUNT; i++) {
            out[i] = idx[i];
        }
        return out;
    }

    /** The 8 corners of a y-rotated cube: index bits (x, y, z) = (bit0, bit1, bit2). */
    public static double[][] corners(double[] centre, double size, double yaw) {
        double[][] out = new double[8][];
        double hs = size / 2;
        for (int k = 0; k < 8; k++) {
            double[] local = {(k & 1) == 0 ? -hs : hs, (k & 2) == 0 ? -hs : hs, (k & 4) == 0 ? -hs : hs};
            double[] r = StageGeometry.rotY(local, yaw);
            out[k] = new double[] {centre[0] + r[0], centre[1] + r[1], centre[2] + r[2]};
        }
        return out;
    }

    /** Cube faces as corner-index quads. */
    public static final int[][] FACES = {
        {0, 1, 3, 2}, {4, 5, 7, 6}, {0, 1, 5, 4}, {2, 3, 7, 6}, {0, 2, 6, 4}, {1, 3, 7, 5},
    };
    /** Cube edges as corner-index pairs. */
    public static final int[][] EDGES = {
        {0, 1}, {2, 3}, {4, 5}, {6, 7}, {0, 2}, {1, 3}, {4, 6}, {5, 7}, {0, 4}, {1, 5}, {2, 6}, {3, 7},
    };

    /** Song time of the latest cut (for the optional screen shake), or -infinity. */
    public double lastCutAt() {
        return lastCut;
    }

    public int destroyedCount() {
        return destroyed;
    }

    public int landedCount() {
        return landed;
    }
}
