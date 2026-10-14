package com.fruitfly.brain;

public final class DarkStateInvariant {
    private final double[][] H;
    private final double lambda2 = 1.0;
    private final double lambdaMinus;
    private final double lambdaPlus;
    private final double[] darkStateVector;
    private final double quadraticSeedResidual;

    public DarkStateInvariant() {
        double a = SovereignConstants.PHI_INV;
        this.H = new double[][] {
            {1.0, a, 0.0},
            {a, 2.0, a},
            {0.0, a, 1.0}
        };
        double disc = 9.0 - 8.0 / SovereignConstants.PHI;
        this.lambdaMinus = (3.0 - Math.sqrt(disc)) / 2.0;
        this.lambdaPlus = (3.0 + Math.sqrt(disc)) / 2.0;
        double invSqrt2 = 1.0 / Math.sqrt(2.0);
        this.darkStateVector = new double[] {invSqrt2, 0.0, -invSqrt2};
        double x = SovereignConstants.PHI;
        this.quadraticSeedResidual = x * x - x - 1.0;
    }

    public double lambda2() { return lambda2; }
    public double lambdaMinus() { return lambdaMinus; }
    public double lambdaPlus() { return lambdaPlus; }
    public double quadraticSeedResidual() { return quadraticSeedResidual; }

    public double eigenvalueResidual() {
        double[] v = darkStateVector;
        double hv0 = H[0][0] * v[0] + H[0][1] * v[1] + H[0][2] * v[2];
        return Math.abs(hv0 / v[0] - 1.0);
    }

    public boolean verify() {
        return Math.abs(quadraticSeedResidual) < 1e-12 && eigenvalueResidual() < 1e-12;
    }
}
