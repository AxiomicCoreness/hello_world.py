package com.fruitfly.games.rhythm.logic;

/**
 * Where things stand on the 3D stage: region label nodes of the fly-brain
 * object and the circuit's neurons around them.
 *
 * DISPLAY ONLY, NOT ANATOMY. The node positions are a hand-made toy layout
 * loosely echoing the label placement in the user's AR screenshot (medulla
 * on top, lamina at the bottom, antennal lobe / mushroom body / central
 * complex on one side, lateral horn / lobula on the other). They are not
 * coordinates from any brain template. Medulla, lamina and central complex
 * are labels only: the toy circuit has no neurons there.
 */
public final class BrainStage {
    /** Region labels, the four lane regions first. */
    public static final String[] REGIONS = {
        "antennal lobe", "mushroom body", "lateral horn", "lobula", "medulla", "lamina", "central complex",
    };
    /** Toy positions (x, y, z), world units; the brain stands on the origin (y = 0 is the ground). */
    private static final double[][] POS = {
        {-0.55, 0.55, 0.25},   // antennal lobe
        {-0.70, 1.35, -0.10},  // mushroom body
        {0.35, 0.70, -0.20},   // lateral horn
        {0.75, 0.95, 0.15},    // lobula
        {0.15, 1.75, 0.05},    // medulla
        {0.10, 0.20, 0.10},    // lamina
        {-0.50, 1.00, 0.35},   // central complex
    };
    /** Centre height of the raw (unscaled) layout. */
    public static final double CENTER_Y = 0.95;
    /** The brain object is shrunk by this factor and seated above the toy fly on the centre tile. */
    public static final double SCALE = 0.3;
    public static final double BASE_Y = 0.78;

    /** Raw layout point -> world: scale about the origin, spin by yaw about y, lift onto the fly. */
    public static double[] place(double[] p, double yaw) {
        double[] r = StageGeometry.rotY(new double[] {p[0] * SCALE, p[1] * SCALE, p[2] * SCALE}, yaw);
        return new double[] {r[0], r[1] + BASE_Y, r[2]};
    }

    private BrainStage() {
    }

    /** Index into {@link #REGIONS}, or -1. */
    public static int regionIndex(String region) {
        if (region == null) {
            return -1;
        }
        for (int i = 0; i < REGIONS.length; i++) {
            if (REGIONS[i].equals(region)) {
                return i;
            }
        }
        return -1;
    }

    public static double[] regionPosition(int r) {
        double[] p = POS[r];
        return new double[] {p[0], p[1], p[2]};
    }

    /** True for the three regions that are labels only (no toy neurons). */
    public static boolean labelOnly(int r) {
        return r >= 4;
    }

    /**
     * Position of neuron i: around its region node, offset by role
     * (".in" lower, ".inter" middle, ".out" upper). Neurons without a known
     * region sit on a ring at the brain's centre height.
     */
    public static double[] neuronPosition(Circuit c, int i) {
        String id = c.id(i);
        double dy = id.endsWith(".in") ? -0.16 : id.endsWith(".out") ? 0.16 : 0.0;
        double dx = id.endsWith(".in") ? -0.08 : id.endsWith(".out") ? 0.08 : 0.0;
        int r = regionIndex(c.region(i));
        if (r >= 0) {
            double[] p = regionPosition(r);
            return new double[] {p[0] + dx, p[1] + dy, p[2]};
        }
        double a = 2.0 * Math.PI * i / Math.max(1, c.neuronCount());
        return new double[] {0.9 * Math.cos(a), CENTER_Y + dy, 0.9 * Math.sin(a)};
    }
}
