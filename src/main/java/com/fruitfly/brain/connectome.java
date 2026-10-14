package com.fruitfly.brain;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Deque;
import java.util.List;
import java.util.Random;

/**
 * 🜁∀ Connectome — CSR adjacency + per-synapse delay ring ∀🜁
 *
 * <p>Synthetic fruit-fly-scale connectome. Deterministic given a seed.
 * No network, no filesystem, no third-party dependencies.
 *
 * <p>CSR layout:
 * <pre>
 *   rowPtr   : int[n + 1]        offsets into colIdx / weight / delayMs
 *   colIdx   : int[nnz]          postsynaptic neuron ids
 *   weight   : double[nnz]       synaptic weight (mV per mV of pre)
 *   delayMs  : double[nnz]       axonal delay per synapse (ms)
 * </pre>
 *
 * <p>Delay ring: one {@link Deque} per synapse. Length is
 * {@code ceil(delayMs[k] / (dt·1000)) + 1}, computed per-call in
 * {@link #currentsFrom(int, double, double)} so a caller can vary dt.
 *
 * <p>Alphabetical order of members is intentional. Reading the class
 * top-down visits every field and method in a stable sequence.
 */
public final class Connectome {

    // ==================================================================
    // Fields
    // ==================================================================

    /** Postsynaptic neuron id for each synapse, in CSR order. */
    private final int[] colIdx;

    /** Axonal delay in milliseconds for each synapse. */
    private final double[] delayMs;

    /** One deque per synapse; ring of recent presynaptic voltages. */
    private final List<Deque<Double>> delayRing;

    /** Number of neurons. */
    private final int n;

    /** Row offsets into colIdx, weight, delayMs; length n + 1. */
    private final int[] rowPtr;

    /** Synaptic weight for each synapse, in CSR order. */
    private final double[] weight;

    // ==================================================================
    // Construction
    // ==================================================================

    /**
     * Construct from explicit CSR arrays.
     *
     * @param n        number of neurons
     * @param rowPtr   row offsets, length {@code n + 1}, monotone
     * @param colIdx   postsynaptic ids, length nnz
     * @param weight   weights, length nnz
     * @param delayMs  delays in milliseconds, length nnz
     */
    public Connectome(final int n,
                      final int[] rowPtr,
                      final int[] colIdx,
                      final double[] weight,
                      final double[] delayMs) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be >= 0");
        }
        if (rowPtr == null || rowPtr.length != n + 1) {
            throw new IllegalArgumentException("rowPtr must be length n + 1");
        }
        if (colIdx == null || weight == null || delayMs == null) {
            throw new IllegalArgumentException("CSR arrays must be non-null");
        }
        if (colIdx.length != weight.length || weight.length != delayMs.length) {
            throw new IllegalArgumentException("CSR arrays must agree on nnz");
        }
        for (int i = 0; i < n; i++) {
            if (rowPtr[i] > rowPtr[i + 1]) {
                throw new IllegalArgumentException("rowPtr must be monotone");
            }
        }

        this.n = n;
        this.rowPtr = Arrays.copyOf(rowPtr, rowPtr.length);
        this.colIdx = Arrays.copyOf(colIdx, colIdx.length);
        this.weight = Arrays.copyOf(weight, weight.length);
        this.delayMs = Arrays.copyOf(delayMs, delayMs.length);

        this.delayRing = new ArrayList<>(colIdx.length);
        for (int k = 0; k < colIdx.length; k++) {
            this.delayRing.add(new ArrayDeque<>());
        }
    }

    /** Convenience constructor: empty connectome of size n. */
    public Connectome(final int n) {
        this(n, zeroRowPtr(n), new int[0], new double[0], new double[0]);
    }

    // ==================================================================
    // Factory — deterministic synthetic connectome
    // ==================================================================

    /**
     * Build a synthetic connectome.
     *
     * <p>For each neuron {@code i}, iterates {@code j = 0 .. n-1}, j != i,
     * and adds an edge {@code i -> j} with probability {@code sparsity}.
     * Weights are uniform in {@code [-1, 1]}. Delays are uniform in
     * {@code [1, 4]} milliseconds. A {@link Random} seeded with
     * {@code seed} guarantees reproducibility across runs and platforms
     * (Java's {@code Random} is specified bit-for-bit in the JLS).
     *
     * @param n         number of neurons
     * @param sparsity  edge probability per ordered pair, in {@code (0, 1)}
     * @param seed      seed for the deterministic {@link Random}
     * @return a connectome with n neurons
     */
    public static Connectome random(final int n,
                                    final double sparsity,
                                    final long seed) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be >= 0");
        }
        if (sparsity <= 0.0 || sparsity >= 1.0) {
            throw new IllegalArgumentException("sparsity must be in (0, 1)");
        }

        final Random rng = new Random(seed);
        final List<Integer> colList = new ArrayList<>();
        final List<Double> wList = new ArrayList<>();
        final List<Double> dList = new ArrayList<>();
        final int[] row = new int[n + 1];

        for (int i = 0; i < n; i++) {
            row[i] = colList.size();
            for (int j = 0; j < n; j++) {
                if (i == j) {
                    continue;
                }
                if (rng.nextDouble() < sparsity) {
                    colList.add(j);
                    // uniform in [-1, 1]
                    wList.add(rng.nextDouble() * 2.0 - 1.0);
                    // uniform in [1, 4] ms
                    dList.add(1.0 + rng.nextDouble() * 3.0);
                }
            }
        }
        row[n] = colList.size();

        final int[] ci = new int[colList.size()];
        for (int k = 0; k < ci.length; k++) {
            ci[k] = colList.get(k);
        }
        final double[] ww = new double[wList.size()];
        for (int k = 0; k < ww.length; k++) {
            ww[k] = wList.get(k);
        }
        final double[] dd = new double[dList.size()];
        for (int k = 0; k < dd.length; k++) {
            dd[k] = dList.get(k);
        }

        return new Connectome(n, row, ci, ww, dd);
    }

    // ==================================================================
    // Current delivery — the wire into LIFRK4
    // ==================================================================

    /**
     * Advance every outgoing synapse from {@code pre} by one tick and
     * return the current arriving at each neuron this tick.
     *
     * <p>Semantics: each call pushes the current presynaptic voltage
     * onto each outgoing synapse's delay ring, trims the ring to the
     * length dictated by that synapse's delay and the caller's
     * {@code dtSeconds}, then delivers {@code weight[k] · peekFirst()}
     * to the postsynaptic neuron.
     *
     * <p>Precondition: {@code 0 <= pre < neuronCount()}.
     * Precondition: {@code dtSeconds > 0}.
     *
     * @param pre          presynaptic neuron index
     * @param preVoltage   its membrane voltage this tick (mV)
     * @param dtSeconds    tick size in seconds
     * @return array length {@code n}; entry {@code j} is the total
     *         current arriving at neuron {@code j} this tick
     */
    public double[] currentsFrom(final int pre,
                                 final double preVoltage,
                                 final double dtSeconds) {
        if (pre < 0 || pre >= n) {
            throw new IllegalArgumentException("pre out of range: " + pre);
        }
        if (dtSeconds <= 0.0) {
            throw new IllegalArgumentException("dtSeconds must be > 0");
        }

        final double[] currents = new double[n];
        final int start = rowPtr[pre];
        final int end   = rowPtr[pre + 1];

        for (int k = start; k < end; k++) {
            final Deque<Double> ring = delayRing.get(k);
            ring.addLast(preVoltage);

            // ring length in samples for this synapse and this dt
            final int ringLen = Math.max(
                    2,
                    (int) Math.ceil(delayMs[k] / (dtSeconds * 1000.0)) + 1);
            while (ring.size() > ringLen) {
                ring.removeFirst();
            }

            final Double head = ring.peekFirst();
            final double delayed = (head == null) ? 0.0 : head;
            currents[colIdx[k]] += weight[k] * delayed;
        }

        return currents;
    }

    // ==================================================================
    // Introspection
    // ==================================================================

    /** Number of neurons. */
    public int neuronCount() {
        return n;
    }

    /** Total number of synapses (nnz). */
    public int synapseCount() {
        return colIdx.length;
    }

    /** Postsynaptic ids reachable from neuron {@code i}, in CSR order. */
    public int[] postsynaptic(final int i) {
        if (i < 0 || i >= n) {
            throw new IllegalArgumentException("i out of range: " + i);
        }
        final int start = rowPtr[i];
        final int end   = rowPtr[i + 1];
        final int[] out = new int[end - start];
        System.arraycopy(colIdx, start, out, 0, out.length);
        return out;
    }

    /** Weights of the synapses from neuron {@code i}, in CSR order. */
    public double[] weightsOf(final int i) {
        if (i < 0 || i >= n) {
            throw new IllegalArgumentException("i out of range: " + i);
        }
        final int start = rowPtr[i];
        final int end   = rowPtr[i + 1];
        final double[] out = new double[end - start];
        System.arraycopy(weight, start, out, 0, out.length);
        return out;
    }

    /** Delays (ms) of the synapses from neuron {@code i}, in CSR order. */
    public double[] delaysOf(final int i) {
        if (i < 0 || i >= n) {
            throw new IllegalArgumentException("i out of range: " + i);
        }
        final int start = rowPtr[i];
        final int end   = rowPtr[i + 1];
        final double[] out = new double[end - start];
        System.arraycopy(delayMs, start, out, 0, out.length);
        return out;
    }

    /** Total outgoing current weighted by weights, ignoring delays. */
    public double sumOutgoingWeights(final int i) {
        if (i < 0 || i >= n) {
            throw new IllegalArgumentException("i out of range: " + i);
        }
        double s = 0.0;
        for (int k = rowPtr[i]; k < rowPtr[i + 1]; k++) {
            s += weight[k];
        }
        return s;
    }

    // ==================================================================
    // Utilities
    // ==================================================================

    /** Row-pointer of zeros, length n + 1. Used by the empty constructor. */
    private static int[] zeroRowPtr(final int n) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be >= 0");
        }
        return new int[n + 1];
    }
}
