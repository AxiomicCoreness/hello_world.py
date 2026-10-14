package com.fruitfly.brain;

/**
 * The Warrior Quadratic — the seed polynomial of the φ-lattice.
 *
 * <pre>
 *     x² − x − 1 = 0
 * </pre>
 *
 * <p>Roots:
 * <pre>
 *     x_+ = (1 + √5) / 2 =  φ      ≈  1.618033988749895
 *     x_- = (1 − √5) / 2 = −φ⁻¹   ≈ −0.618033988749895
 * </pre>
 *
 * <p>Vieta:
 * <pre>
 *     sum     x_+ + x_-  =  1
 *     product x_+ · x_-  = −1
 *     disc    b² − 4ac   =  5
 *     vertex  −b / 2a    =  1/2
 * </pre>
 *
 * <p>The positive root is {@link SovereignConstants#PHI}. This class is the
 * algebraic seed from which the trimer Hamiltonian in
 * {@link DarkStateInvariant} derives its φ⁻¹ entries.
 *
 * <p>Not a general-purpose quadratic solver — this is the specific seed. It
 * carries its coefficients, roots, and Vieta residuals as named fields so
 * downstream code can verify the seed without re-deriving it.
 */
public final class WarriorQuadratic {

    /** Coefficients of x² − x − 1 = 0. */
    public static final double A =  1.0;
    public static final double B = -1.0;
    public static final double C = -1.0;

    /** Exact discriminant: b² − 4ac = 1 + 4 = 5. */
    public static final double DISCRIMINANT = 5.0;

    private WarriorQuadratic() { /* no instances */ }

    /** Positive root φ. */
    public static double positiveRoot() {
        return (-B + Math.sqrt(DISCRIMINANT)) / (2.0 * A);
    }

    /** Negative root ψ = −φ⁻¹. */
    public static double negativeRoot() {
        return (-B - Math.sqrt(DISCRIMINANT)) / (2.0 * A);
    }

    /** Evaluate p(x) = a x² + b x + c at x. */
    public static double evaluate(double x) {
        return A * x * x + B * x + C;
    }

    /** Residual of Vieta's sum:  (x_+ + x_-) − (−b/a). */
    public static double sumResidual() {
        return Math.abs((positiveRoot() + negativeRoot()) - (-B / A));
    }

    /** Residual of Vieta's product:  (x_+ · x_-) − (c/a). */
    public static double productResidual() {
        return Math.abs((positiveRoot() * negativeRoot()) - (C / A));
    }

    /** Residual of p(φ):  should be 0. */
    public static double seedResidual() {
        return Math.abs(evaluate(positiveRoot()));
    }

    /** Vertex x-coordinate, −b/(2a) = 1/2. */
    public static double vertexX() {
        return -B / (2.0 * A);
    }

    /**
     * All four invariants hold to {@code tol}: seed, sum, product, and the
     * positive root equals {@link SovereignConstants#PHI}.
     */
    public static boolean verify(double tol) {
        return seedResidual()    < tol
            && sumResidual()     < tol
            && productResidual() < tol
            && Math.abs(positiveRoot() - SovereignConstants.PHI) < tol;
    }

    /** Convenience: verify at 1e-12. */
    public static boolean verify() {
        return verify(1e-12);
    }
}
