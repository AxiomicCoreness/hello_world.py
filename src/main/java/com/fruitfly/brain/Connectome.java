package com.fruitfly.brain;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Deque;
import java.util.List;
import java.util.Random;

/**
 * CSR adjacency + per-synapse delay ring.
 *
 * Synthetic fruit-fly-scale connectome. Deterministic given a seed.
 * No network, no filesystem, no third-party dependencies.
 */
public final class Connectome {

    private final int[] colIdx;
    private final double[] delayMs;
    private final List<Deque<Double>> delayRing;
    private final int n;
    private final int[] rowPtr;
    private final double[] weight;

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

    public Connectome(final int n) {
        this(n, zeroRowPtr(n), new int[0], new double[0], new double[0]);
    }

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
                    wList.add(rng.nextDouble() * 2.0 - 1.0);
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

    public int neuronCount() {
        return n;
    }

    public int synapseCount() {
        return colIdx.length;
    }

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

    private static int[] zeroRowPtr(final int n) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be >= 0");
        }
        return new int[n + 1];
    }
}
