package com.fruitfly.games.rhythm.logic;

/** Small 3D helpers for the stage: vectors, oriented boxes, and capsule (segment + radius) vs cube tests. */
public final class StageGeometry {
    /** Box corner index = bx + 2*by + 4*bz for the -/+ side of each axis. */
    public static final int[][] EDGES = {
        {0, 1}, {2, 3}, {4, 5}, {6, 7}, {0, 2}, {1, 3}, {4, 6}, {5, 7}, {0, 4}, {1, 5}, {2, 6}, {3, 7},
    };
    public static final int[][] FACES = {
        {0, 1, 3, 2}, {4, 5, 7, 6}, {0, 1, 5, 4}, {2, 3, 7, 6}, {0, 2, 6, 4}, {1, 3, 7, 5},
    };

    private StageGeometry() {
    }

    public static double dot(double[] a, double[] b) {
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    }

    public static double[] cross(double[] a, double[] b) {
        return new double[] {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
    }

    public static double[] normalize(double[] a) {
        double l = Math.sqrt(dot(a, a));
        return new double[] {a[0] / l, a[1] / l, a[2] / l};
    }

    public static double[] sub(double[] a, double[] b) {
        return new double[] {a[0] - b[0], a[1] - b[1], a[2] - b[2]};
    }

    public static double distance(double[] a, double[] b) {
        double[] d = sub(a, b);
        return Math.sqrt(dot(d, d));
    }

    /** 8 corners of the box centred at c with orthonormal axes ax, ay, az and half extents hx, hy, hz. */
    public static double[][] box(double[] c, double[] ax, double[] ay, double[] az, double hx, double hy, double hz) {
        double[][] out = new double[8][];
        for (int i = 0; i < 8; i++) {
            double sx = (i & 1) == 0 ? -hx : hx;
            double sy = (i & 2) == 0 ? -hy : hy;
            double sz = (i & 4) == 0 ? -hz : hz;
            out[i] = new double[] {
                c[0] + sx * ax[0] + sy * ay[0] + sz * az[0],
                c[1] + sx * ax[1] + sy * ay[1] + sz * az[1],
                c[2] + sx * ax[2] + sy * ay[2] + sz * az[2],
            };
        }
        return out;
    }

    /** Axis-aligned cube corners (edge {@code size}). */
    public static double[][] cube(double[] c, double size) {
        double h = size / 2.0;
        return box(c, new double[] {1, 0, 0}, new double[] {0, 1, 0}, new double[] {0, 0, 1}, h, h, h);
    }

    /** Rotate (x, y, z) about the vertical axis by {@code yaw} radians. */
    public static double[] rotY(double[] p, double yaw) {
        double c = Math.cos(yaw);
        double s = Math.sin(yaw);
        return new double[] {c * p[0] + s * p[2], p[1], -s * p[0] + c * p[2]};
    }

    /**
     * Does the capsule from a to b with radius r touch a cube of edge
     * {@code size} centred at {@code centre}, rotated by {@code yaw} about y?
     * Exact: the segment is moved into the cube's frame and tested against the
     * box grown by r (a slab test), which is conservative only at the box's
     * rounded corners (a few % of r).
     */
    public static boolean capsuleHitsCube(double[] a, double[] b, double r, double[] centre, double size, double yaw) {
        double[] la = rotY(new double[] {a[0] - centre[0], a[1] - centre[1], a[2] - centre[2]}, -yaw);
        double[] lb = rotY(new double[] {b[0] - centre[0], b[1] - centre[1], b[2] - centre[2]}, -yaw);
        double h = size / 2.0 + r;
        double t0 = 0.0;
        double t1 = 1.0;
        for (int k = 0; k < 3; k++) {
            double d = lb[k] - la[k];
            if (Math.abs(d) < 1e-12) {
                if (la[k] < -h || la[k] > h) {
                    return false;
                }
                continue;
            }
            double u0 = (-h - la[k]) / d;
            double u1 = (h - la[k]) / d;
            if (u0 > u1) {
                double tmp = u0;
                u0 = u1;
                u1 = tmp;
            }
            t0 = Math.max(t0, u0);
            t1 = Math.min(t1, u1);
            if (t0 > t1) {
                return false;
            }
        }
        return true;
    }
}
