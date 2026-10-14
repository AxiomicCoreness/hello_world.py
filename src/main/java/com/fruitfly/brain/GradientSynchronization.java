package com.fruitfly.brain;

/**
 * Hebbian update with eta = 1 (full replacement, then row-L2 normalize).
 *
 * Dependency-free except SovereignConstants.ETA_UNITY.
 */
public final class GradientSynchronization {

    private GradientSynchronization() {}

    /**
     * T_ij <- T_ij + eta * s_i * s_j, then row-L2 normalize.
     * eta = 1 makes this a full-replacement update.
     */
    public static void gradientSynchronizationPriority(double[] voltages, double[][] tensor) {
        if (voltages == null || tensor == null) {
            throw new IllegalArgumentException("voltages and tensor must be non-null");
        }
        int n = voltages.length;
        if (tensor.length != n) {
            throw new IllegalArgumentException("tensor row count must match voltages");
        }
        double eta = SovereignConstants.ETA_UNITY;
        for (int i = 0; i < n; i++) {
            if (tensor[i].length != n) {
                throw new IllegalArgumentException("tensor must be square");
            }
            for (int j = 0; j < n; j++) {
                tensor[i][j] += eta * voltages[i] * voltages[j];
            }
            double norm = 0.0;
            for (int j = 0; j < n; j++) {
                norm += tensor[i][j] * tensor[i][j];
            }
            norm = Math.sqrt(norm);
            if (norm > 0.0) {
                for (int j = 0; j < n; j++) {
                    tensor[i][j] /= norm;
                }
            }
        }
    }
}
