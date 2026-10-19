package com.fruitfly.brain;

import java.util.ArrayList;
import java.util.List;

/**
 * Holds a connectome and a swarm of LIFRK4 neurons.
 *
 * Uses the existing LIFRK4.stepTick contract. Does not require LIFRK4
 * to implement Neuron. Gate is DarkStateInvariant.verify.
 */
public final class SovereignAutomaton {

    private final Connectome connectome;
    private final List<LIFRK4> swarm;
    private final DarkStateInvariant dark;
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
        this.dark = new DarkStateInvariant();
        this.state = SovereigntyState.OBSERVATION;
        this.time = 0.0;
    }

    public void step(double dt, double drive) {
        if (!dark.verify()) {
            throw new IllegalStateException("dark-state gate refused");
        }
        int n = swarm.size();
        // Gather every presynaptic neuron's delayed output first, indexed by
        // postsynaptic target, so all neurons see the same pre-step voltages.
        double[] incoming = new double[n];
        for (int i = 0; i < n; i++) {
            double[] currents = connectome.currentsFrom(i, swarm.get(i).v(), dt);
            for (int j = 0; j < n; j++) {
                incoming[j] += currents[j];
            }
        }
        for (int j = 0; j < n; j++) {
            swarm.get(j).stepTick(incoming[j] + drive);
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

    public double time() { return time; }
    public SovereigntyState state() { return state; }
    public List<LIFRK4> swarm() { return swarm; }
    public Connectome connectome() { return connectome; }
    public boolean gate() { return dark.verify(); }
}
