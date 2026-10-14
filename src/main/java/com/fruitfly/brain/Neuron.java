package com.fruitfly.brain;

import java.util.function.DoubleUnaryOperator;

/**
 * Contract that {@link SovereignAutomaton} requires of any neuron type.
 *
 * <p>LIFRK4 must satisfy this interface for the automaton to compile.
 * If LIFRK4 does not implement it, the mismatch is visible at compile
 * time, not at runtime.
 */
public interface Neuron {

    /** Current membrane voltage (mV). */
    double voltage();

    /** True if the neuron fired during the most recent step(). */
    boolean firedThisStep();

    /** Number of spikes emitted since construction (or since reset()). */
    long spikeCount();

    /** Reset to resting state. Zeroes spikeCount(). */
    void reset();

    /**
     * Advance one macro-tick of size dt seconds.
     *
     * @param t     current time (seconds)
     * @param dt    step size (seconds)
     * @param input synaptic current as a function of time (μA)
     * @return      true if the neuron fired during this call
     */
    boolean step(double t, double dt, DoubleUnaryOperator input);
}
