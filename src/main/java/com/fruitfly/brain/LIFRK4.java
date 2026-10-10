package com.fruitfly.brain;

/**
 * Runge-Kutta 4 integrator for a leaky integrate-and-fire neuron.
 *
 * <p>Unexecuted draft, co-created from the pasted specification and
 * javac-compiled in the sandbox (JDK 17 present). No correctness claim
 * beyond compilation: it still needs a fixture run on the S0 side.
 *
 * <p>Constants are pinned from a prior pasted LIF spec, NOT verified
 * against Shiu et al.
 */
public final class LIFRK4 {

    public static final double V_REST   = -52.0;
    public static final double V_THRESH = -45.0;
    public static final double V_RESET  = -52.0;
    public static final double TAU_V    = 20.0;
    public static final double TAU_G    = 5.0;
    public static final double REFRAC   = 2.2;
    public static final double SYNAPTIC_GAIN = 0.275;
    public static final double BRAIN_TICK_MS  = 50.0;

    /** Placeholder substep count: 50 substeps of 1.0 ms per tick. */
    public static final int SUBSTEPS = 50;

    private double v = V_REST;
    private double g = 0.0;
    private double refractoryRemaining = 0.0;

    public double v() { return v; }
    public double g() { return g; }

    /** Advance one brain tick. gDelta = summed synaptic input (mV) this tick. */
    public void stepTick(double gDelta) {
        double dt = BRAIN_TICK_MS / SUBSTEPS;
        for (int i = 0; i < SUBSTEPS; i++) {
            stepRK4(dt);
            if (refractoryRemaining > 0.0) {
                refractoryRemaining -= dt;
                if (refractoryRemaining < 0.0) {
                    refractoryRemaining = 0.0;
                }
            }
        }
        g += gDelta;
        if (v >= V_THRESH && refractoryRemaining == 0.0) {
            v = V_RESET;
            refractoryRemaining = REFRAC;
        }
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
