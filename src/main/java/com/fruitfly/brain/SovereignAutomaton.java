package com.fruitfly.brain;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Holds a connectome and a swarm of LIFRK4 neurons.
 *
 * Uses the per-substep LIFRK4.stepTick(double[]) contract. Does not require
 * LIFRK4 to implement Neuron. Gate is DarkStateInvariant.verify.
 *
 * Synaptic input is scheduled on the neuron's substep grid
 * (dt = BRAIN_TICK_MS / SUBSTEPS ms): a presynaptic voltage sampled at the
 * start of a tick reaches its target at substep ceil(delayMs / dt) after it,
 * carried into later ticks when the delay exceeds one tick. External drive
 * lands at substep 0.
 */
public final class SovereignAutomaton {

    private final Connectome connectome;
    private final List<LIFRK4> swarm;
    private final DarkStateInvariant dark;
    /** pending[j][s]: input for neuron j at substep s from the current tick start. */
    private final double[][] pending;
    private SovereigntyState state;
    private double time;

    public SovereignAutomaton(Connectome connectome, int n) {
        if (connectome == null) {
            throw new IllegalArgumentException("connectome must be non-null");
        }
        if (n != connectome.neuronCount()) {
            throw new IllegalArgumentException("n must match connectome.neuronCount");
        }
        this.connectome = connectome;
        this.swarm = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            this.swarm.add(new LIFRK4());
        }
        int horizon = LIFRK4.SUBSTEPS;
        for (int i = 0; i < n; i++) {
            for (double d : connectome.delaysOf(i)) {
                horizon = Math.max(horizon, delaySubsteps(d) + LIFRK4.SUBSTEPS);
            }
        }
        this.pending = new double[n][horizon];
        this.dark = new DarkStateInvariant();
        this.state = SovereigntyState.OBSERVATION;
        this.time = 0.0;
    }

    public void step(double dt, double drive) {
        if (!dark.verify()) {
            throw new IllegalStateException("dark-state gate refused");
        }
        int n = swarm.size();
        // Schedule every presynaptic neuron's output first, at the substep its
        // delay lands on, so all neurons see the same pre-step voltages.
        for (int i = 0; i < n; i++) {
            double vPre = swarm.get(i).v();
            int[] post = connectome.postsynaptic(i);
            double[] w = connectome.weightsOf(i);
            double[] d = connectome.delaysOf(i);
            for (int k = 0; k < post.length; k++) {
                pending[post[k]][delaySubsteps(d[k])] += w[k] * vPre;
            }
        }
        for (int j = 0; j < n; j++) {
            double[] p = pending[j];
            p[0] += drive;
            swarm.get(j).stepTick(Arrays.copyOf(p, LIFRK4.SUBSTEPS));
            System.arraycopy(p, LIFRK4.SUBSTEPS, p, 0, p.length - LIFRK4.SUBSTEPS);
            Arrays.fill(p, p.length - LIFRK4.SUBSTEPS, p.length, 0.0);
        }
        time += dt;
        if (!state.isAbsorbing()) {
            state = state.next();
        }
    }

    public String respond(String chat, double q, double p) {
        if (chat == null || chat.isEmpty()) {
            return "";
        }
        step(1e-4, 0.5);
        return String.format("phase=%s q=%.4f p=%.4f t=%.6f", state, q, p, time);
    }

    /** Substep index a delay of delayMs lands on: ceil(delayMs / dt). */
    static int delaySubsteps(double delayMs) {
        double dt = LIFRK4.BRAIN_TICK_MS / LIFRK4.SUBSTEPS;
        return Math.max(0, (int) Math.ceil(delayMs / dt - 1e-9));
    }

    public double time() { return time; }
    public SovereigntyState state() { return state; }
    public List<LIFRK4> swarm() { return swarm; }
    public Connectome connectome() { return connectome; }
    public boolean gate() { return dark.verify(); }
}
