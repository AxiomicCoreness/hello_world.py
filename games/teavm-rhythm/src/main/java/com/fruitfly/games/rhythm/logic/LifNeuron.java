package com.fruitfly.games.rhythm.logic;

/**
 * Leaky integrate-and-fire neuron with an RK4 integrator.
 *
 * Ported from the root project's src/main/java/com/fruitfly/brain/LIFRK4.java
 * at fca08122 (blob 44ded4a3, "LIFRK4 spike check per substep"). This game is
 * a standalone Maven project and can't depend on com.fruitfly.brain, so the
 * math is copied operation for operation: the same constants, the same RK4
 * step for (v, g), the same refractory countdown and clamp (2.2 - 1 - 1 leaves
 * 0.20000000000000018, which the next substep clamps to 0), the same
 * threshold check after every substep, and both stepTick variants with
 * LIFRK4's input timing. The one addition is that
 * {@link #substep(double, double)} reports whether that substep spiked, so
 * the autoplayer can turn a spike into a key press at that exact time.
 *
 * LifRk4ParityTest checks this port against golden traces generated from the
 * real LIFRK4 (tools/LifGoldenTraceGen.java) to 1e-12.
 *
 * Like the original, the constants come from a pasted LIF spec and are not
 * verified against Shiu et al.
 */
public final class LifNeuron {
    public static final double V_REST = -52.0;
    public static final double V_THRESH = -45.0;
    public static final double V_RESET = -52.0;
    public static final double TAU_V = 20.0;
    public static final double TAU_G = 5.0;
    public static final double REFRAC = 2.2;
    /** Unused by the dynamics; kept so the constant set mirrors LIFRK4. */
    public static final double SYNAPTIC_GAIN = 0.275;
    public static final double BRAIN_TICK_MS = 50.0;
    public static final int SUBSTEPS = 50;
    /** Substep length, 1 ms. */
    public static final double DT_MS = BRAIN_TICK_MS / SUBSTEPS;

    private double v = V_REST;
    private double g = 0.0;
    private double refractoryRemaining = 0.0;

    public double v() {
        return v;
    }

    public double g() {
        return g;
    }

    public double refractoryRemaining() {
        return refractoryRemaining;
    }

    /**
     * One substep, as in LIFRK4: add {@code gDelta} to g, integrate dt, count
     * down the refractory period, then check the threshold.
     *
     * @return true if the neuron spiked during this substep
     */
    public boolean substep(double gDelta, double dt) {
        g += gDelta;
        stepRK4(dt);
        if (refractoryRemaining > 0.0) {
            refractoryRemaining -= dt;
            if (refractoryRemaining < 0.0) {
                refractoryRemaining = 0.0;
            }
        }
        if (v >= V_THRESH && refractoryRemaining == 0.0) {
            v = V_RESET;
            refractoryRemaining = REFRAC;
            return true;
        }
        return false;
    }

    /**
     * LIFRK4.stepTick(double) equivalent: 50 substeps with no input, then
     * {@code gDelta} is added to g after the tick, so it first acts next tick.
     * Returns the number of spikes in the tick.
     */
    public int stepTick(double gDelta) {
        int spikes = 0;
        for (int i = 0; i < SUBSTEPS; i++) {
            if (substep(0.0, DT_MS)) {
                spikes++;
            }
        }
        g += gDelta;
        return spikes;
    }

    /**
     * LIFRK4.stepTick(double[]) equivalent: gDeltaPerSubstep[s] is added to g
     * at the start of substep s. Returns the number of spikes in the tick.
     */
    public int stepTick(double[] gDeltaPerSubstep) {
        if (gDeltaPerSubstep == null || gDeltaPerSubstep.length != SUBSTEPS) {
            throw new IllegalArgumentException("gDeltaPerSubstep must have length SUBSTEPS = " + SUBSTEPS);
        }
        int spikes = 0;
        for (int i = 0; i < SUBSTEPS; i++) {
            if (substep(gDeltaPerSubstep[i], DT_MS)) {
                spikes++;
            }
        }
        return spikes;
    }

    private void stepRK4(double dt) {
        if (refractoryRemaining > 0.0) {
            v = V_RESET;
            double k1 = -g / TAU_G;
            double k2 = -(g + 0.5 * dt * k1) / TAU_G;
            double k3 = -(g + 0.5 * dt * k2) / TAU_G;
            double k4 = -(g + dt * k3) / TAU_G;
            g += dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0;
            return;
        }
        double k1v = dvdt(v, g);
        double k1g = dgdt(g);
        double k2v = dvdt(v + 0.5 * dt * k1v, g + 0.5 * dt * k1g);
        double k2g = dgdt(g + 0.5 * dt * k1g);
        double k3v = dvdt(v + 0.5 * dt * k2v, g + 0.5 * dt * k2g);
        double k3g = dgdt(g + 0.5 * dt * k2g);
        double k4v = dvdt(v + dt * k3v, g + dt * k3g);
        double k4g = dgdt(g + dt * k3g);
        v += dt * (k1v + 2.0 * k2v + 2.0 * k3v + k4v) / 6.0;
        g += dt * (k1g + 2.0 * k2g + 2.0 * k3g + k4g) / 6.0;
    }

    private static double dvdt(double v, double g) {
        return (V_REST - v + g) / TAU_V;
    }

    private static double dgdt(double g) {
        return -g / TAU_G;
    }
}
