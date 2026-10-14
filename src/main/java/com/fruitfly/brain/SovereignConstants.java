package com.fruitfly.brain;

/**
 * Namespace for φ and its powers.
 *
 * <p>The seed polynomial of the φ-lattice is
 * <pre>    x² − x − 1 = 0    </pre>
 * whose positive root is φ. This class carries φ and the derived
 * constants used across the sovereign brain model.
 *
 * <p>All values are double precision. {@link #PHI} is computed from the
 * closed form (1 + √5) / 2; {@link #PHI_INV} uses the exact identity
 * φ⁻¹ = φ − 1 rather than rounding a division.
 */
public final class SovereignConstants {

    private SovereignConstants() { /* no instances */ }

    /** The golden ratio, φ = (1 + √5) / 2 ≈ 1.618033988749895. */
    public static final double PHI = (1.0 + Math.sqrt(5.0)) / 2.0;

    /** φ⁻¹ = φ − 1 ≈ 0.618033988749895. */
    public static final double PHI_INV = PHI - 1.0;

    /** Powers of φ: φ² = φ + 1, φ³ = 2φ + 1, … */
    public static final double PHI2 = PHI * PHI;
    public static final double PHI3 = PHI2 * PHI;
    public static final double PHI4 = PHI3 * PHI;
    public static final double PHI5 = PHI4 * PHI;
    public static final double PHI6 = PHI5 * PHI;
    public static final double PHI7 = PHI6 * PHI;
    public static final double PHI8 = PHI7 * PHI;
    public static final double PHI9 = PHI8 * PHI;

    /** Deep negative powers of φ (underflow toward zero in double). */
    public static final double PHI_MINUS_709 = Math.pow(PHI, -709.0);
    public static final double PHI_MINUS_1418 = Math.pow(PHI, -1418.0);

    /** The non-asymptotic unity, 0.9̄ ≡ 1. */
    public static final double ETA_UNITY = 1.0;
}
