package com.fruitfly.games.rhythm.logic;

import java.util.Arrays;

/**
 * Runs a {@link Circuit} of {@link LifNeuron}s on the 1 ms substep grid.
 *
 * Delivery timing is SovereignAutomaton's rule (root
 * src/main/java/com/fruitfly/brain/SovereignAutomaton.java): a synapse with
 * delay d ms delivers {@link #delaySubsteps(double) ceil(d / dt)} substeps
 * after the presynaptic sample point, into a pending buffer that carries
 * over tick boundaries, so delays &gt; 50 ms land in a later tick. The sample
 * point is the end of a substep (= the start of the next, which is where
 * SovereignAutomaton samples at a tick start). So a spike detected in
 * substep s lands at the start of substep s + 1 + ceil(d / dt).
 *
 * One deliberate difference: what is delivered. SovereignAutomaton adds
 * w * vPre (presynaptic voltage, about -52 mV at rest) once per 50 ms tick;
 * that turns every positive weight into a constant negative drive and can't
 * carry a timed cue. Here a presynaptic SPIKE adds w to the target's g, so
 * weight is a conductance kick in the same units as LifAutoplayer.DRIVE_G.
 */
public final class CircuitSim {
    private final Circuit circuit;
    private final LifNeuron[] neurons;
    private final double[][] pending;
    private final int[] synSlots;
    private final long[] lastSpike;
    private final long[] perNeuron;
    private int head;
    private long substeps;
    private long spikes;

    public CircuitSim(Circuit circuit) {
        this.circuit = circuit;
        int n = circuit.neuronCount();
        neurons = new LifNeuron[n];
        for (int i = 0; i < n; i++) {
            neurons[i] = new LifNeuron();
        }
        synSlots = new int[circuit.synapseCount()];
        int max = 0;
        for (int k = 0; k < synSlots.length; k++) {
            synSlots[k] = delaySubsteps(circuit.delayMs(k));
            max = Math.max(max, synSlots[k]);
        }
        pending = new double[n][max + 2];
        lastSpike = new long[n];
        perNeuron = new long[n];
        Arrays.fill(lastSpike, Long.MIN_VALUE);
    }

    /** Substep a delay of delayMs lands on: ceil(delayMs / dt), as SovereignAutomaton.delaySubsteps. */
    public static int delaySubsteps(double delayMs) {
        return Math.max(0, (int) Math.ceil(delayMs / LifNeuron.DT_MS - 1e-9));
    }

    /**
     * Advance one 1 ms substep. {@code external[i]} (may be null) is added to
     * neuron i's g at the start of the substep, alongside synaptic input due
     * now. Returns which neurons spiked in this substep.
     */
    public boolean[] step(double[] external) {
        int n = neurons.length;
        int h = pending.length == 0 ? 0 : pending[0].length;
        boolean[] spiked = new boolean[n];
        for (int j = 0; j < n; j++) {
            double in = pending[j][head] + (external == null ? 0.0 : external[j]);
            pending[j][head] = 0.0;
            spiked[j] = neurons[j].substep(in, LifNeuron.DT_MS);
        }
        for (int i = 0; i < n; i++) {
            if (!spiked[i]) {
                continue;
            }
            spikes++;
            lastSpike[i] = substeps;
            perNeuron[i]++;
            for (int k = circuit.rowStart(i); k < circuit.rowEnd(i); k++) {
                pending[circuit.target(k)][(head + 1 + synSlots[k]) % h] += circuit.weight(k);
            }
        }
        if (h > 0) {
            head = (head + 1) % h;
        }
        substeps++;
        return spiked;
    }

    public Circuit circuit() {
        return circuit;
    }

    public LifNeuron neuron(int i) {
        return neurons[i];
    }

    /** Substeps run so far (1 ms each). */
    public long substeps() {
        return substeps;
    }

    public long spikeCount() {
        return spikes;
    }

    /** Substep index of neuron i's last spike, or Long.MIN_VALUE if it never spiked. */
    public long lastSpikeSubstep(int i) {
        return lastSpike[i];
    }

    /** Spikes neuron i has fired so far. */
    public long spikeCount(int i) {
        return perNeuron[i];
    }
}
