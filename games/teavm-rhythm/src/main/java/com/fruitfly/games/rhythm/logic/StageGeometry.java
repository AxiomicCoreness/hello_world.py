package com.fruitfly.games.rhythm.logic;

/** Small 3D helpers for the stage: y-rotation and capsule (segment + radius) vs y-rotated cube tests. */
public final class StageGeometry {
    private StageGeometry() {
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
