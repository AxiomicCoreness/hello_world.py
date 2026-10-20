package com.fruitfly.games.rhythm.logic;

/**
 * Pure pseudo-3D math for the stage that holds the fly-brain object.
 *
 * An orbit camera sits at distance d from a target point above the origin
 * anchor, at elevation {@code pitch} and orbit angle {@code yaw} around the
 * vertical axis, and looks at the target through a proper lookAt basis:
 * forward = normalise(target - eye), right = normalise(forward x worldUp),
 * up = right x forward. A world point p is expressed in that basis
 * (xc, yc, zc) = ((p-eye)·right, (p-eye)·up, (p-eye)·forward), culled if
 * zc is not beyond the near plane, then pinhole-projected with one focal
 * length for both axes (square pixels, so any canvas aspect is correct).
 * Segments crossing the near plane are clipped, not dropped.
 *
 * World axes: x right, y up, z towards the viewer at yaw 0. Ground is y = 0;
 * the brain stands on the origin. No browser types here.
 */
public final class Scene3D {
    /** One full orbit every 40 s of song time. */
    public static final double ORBIT_PERIOD_MS = 40_000.0;
    public static final double NEAR = 0.05;

    private final double[] eye = new double[3];
    private final double[] right = new double[3];
    private final double[] up = new double[3];
    private final double[] fwd = new double[3];
    private final double focalPx;
    private final double cx;
    private final double cy;

    /**
     * @param yaw      orbit angle around +y, radians
     * @param pitch    camera elevation above the target, radians, |pitch| &lt; pi/2
     * @param distance camera distance from the target (&gt; NEAR)
     * @param focalPx  focal length in canvas px (same for x and y)
     * @param cx       screen x of the target
     * @param cy       screen y of the target
     * @param targetY  world height the camera looks at (target = (0, targetY, 0))
     */
    public Scene3D(double yaw, double pitch, double distance, double focalPx, double cx, double cy, double targetY) {
        if (!(distance > NEAR) || !(focalPx > 0) || !(Math.abs(pitch) < Math.PI / 2)) {
            throw new IllegalArgumentException("need distance > NEAR, focalPx > 0, |pitch| < pi/2");
        }
        double cp = Math.cos(pitch);
        eye[0] = distance * cp * Math.sin(yaw);
        eye[1] = targetY + distance * Math.sin(pitch);
        eye[2] = distance * cp * Math.cos(yaw);
        fwd[0] = -eye[0] / distance;
        fwd[1] = (targetY - eye[1]) / distance;
        fwd[2] = -eye[2] / distance;
        // right = fwd x (0,1,0) = (-fwd.z, 0, fwd.x), normalised
        double rl = Math.hypot(fwd[2], fwd[0]);
        right[0] = -fwd[2] / rl;
        right[1] = 0.0;
        right[2] = fwd[0] / rl;
        // up = right x fwd
        up[0] = right[1] * fwd[2] - right[2] * fwd[1];
        up[1] = right[2] * fwd[0] - right[0] * fwd[2];
        up[2] = right[0] * fwd[1] - right[1] * fwd[0];
        this.focalPx = focalPx;
        this.cx = cx;
        this.cy = cy;
    }

    /** Focal length for a vertical field of view over a canvas height. */
    public static double focalForFov(double fovYRad, double heightPx) {
        return heightPx / 2.0 / Math.tan(fovYRad / 2.0);
    }

    /** Orbit yaw as a pure function of song time: 2 pi per {@link #ORBIT_PERIOD_MS}, in [0, 2 pi). */
    public static double orbitYaw(double songTimeMs) {
        double turns = songTimeMs / ORBIT_PERIOD_MS;
        return (turns - Math.floor(turns)) * 2.0 * Math.PI;
    }

    /** World point to camera space {xc, yc, zc} (zc = depth along the view axis). */
    public double[] toCamera(double x, double y, double z) {
        double dx = x - eye[0];
        double dy = y - eye[1];
        double dz = z - eye[2];
        return new double[] {
            dx * right[0] + dy * right[1] + dz * right[2],
            dx * up[0] + dy * up[1] + dz * up[2],
            dx * fwd[0] + dy * fwd[1] + dz * fwd[2],
        };
    }

    public double[] eye() {
        return eye.clone();
    }

    /** {screenX, screenY, depth, pxPerUnit}, or null if not beyond the near plane. */
    public double[] project(double x, double y, double z) {
        double[] c = toCamera(x, y, z);
        return c[2] <= NEAR ? null : screen(c);
    }

    private double[] screen(double[] c) {
        double s = focalPx / c[2];
        return new double[] {cx + c[0] * s, cy - c[1] * s, c[2], s};
    }

    /**
     * Project a segment, clipping it at the near plane. Returns
     * {x0, y0, x1, y1} in screen px, or null if it's entirely behind.
     */
    public double[] projectSegment(double[] a, double[] b) {
        double[] ca = toCamera(a[0], a[1], a[2]);
        double[] cb = toCamera(b[0], b[1], b[2]);
        boolean ina = ca[2] > NEAR;
        boolean inb = cb[2] > NEAR;
        if (!ina && !inb) {
            return null;
        }
        if (!ina || !inb) {
            double t = (NEAR + 1e-9 - ca[2]) / (cb[2] - ca[2]);
            double[] m = {ca[0] + t * (cb[0] - ca[0]), ca[1] + t * (cb[1] - ca[1]), NEAR + 1e-9};
            if (!ina) {
                ca = m;
            } else {
                cb = m;
            }
        }
        double[] pa = screen(ca);
        double[] pb = screen(cb);
        return new double[] {pa[0], pa[1], pb[0], pb[1]};
    }
}
