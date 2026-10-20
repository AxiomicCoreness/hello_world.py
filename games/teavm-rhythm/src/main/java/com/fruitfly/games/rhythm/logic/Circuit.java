package com.fruitfly.games.rhythm.logic;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * A parsed connectome: neurons (id, optional region label) and synapses in
 * CSR order (rows by source index, document order within a row), exactly as
 * the root ConnectomeLoader builds them. Immutable.
 */
public final class Circuit {
    private final String[] ids;
    private final String[] regions;
    private final int[] rowPtr;
    private final int[] colIdx;
    private final double[] weight;
    private final double[] delayMs;
    private final Map<String, Integer> index = new HashMap<>();

    Circuit(List<String> ids, List<String> regions, int[] rowPtr, int[] colIdx, double[] weight, double[] delayMs) {
        this.ids = ids.toArray(new String[0]);
        this.regions = regions.toArray(new String[0]);
        this.rowPtr = rowPtr;
        this.colIdx = colIdx;
        this.weight = weight;
        this.delayMs = delayMs;
        for (int i = 0; i < this.ids.length; i++) {
            index.put(this.ids[i], i);
        }
    }

    public int neuronCount() {
        return ids.length;
    }

    public int synapseCount() {
        return colIdx.length;
    }

    public String id(int i) {
        return ids[i];
    }

    /** Region label, or null if the neuron has none. */
    public String region(int i) {
        return regions[i];
    }

    /** Index of a neuron id, or -1. */
    public int indexOf(String id) {
        Integer i = index.get(id);
        return i == null ? -1 : i;
    }

    public int rowStart(int pre) {
        return rowPtr[pre];
    }

    public int rowEnd(int pre) {
        return rowPtr[pre + 1];
    }

    /** Postsynaptic index of synapse k (CSR order). */
    public int target(int k) {
        return colIdx[k];
    }

    public double weight(int k) {
        return weight[k];
    }

    public double delayMs(int k) {
        return delayMs[k];
    }

    /** Presynaptic index of synapse k. */
    public int source(int k) {
        for (int i = 0; i < ids.length; i++) {
            if (k < rowPtr[i + 1]) {
                return i;
            }
        }
        throw new IndexOutOfBoundsException("synapse " + k);
    }

    int[] rowPtr() {
        return Arrays.copyOf(rowPtr, rowPtr.length);
    }
}
