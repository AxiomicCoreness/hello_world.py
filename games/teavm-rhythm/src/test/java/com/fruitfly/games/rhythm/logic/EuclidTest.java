package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Bjorklund's algorithm against the published patterns (Toussaint 2005), and the rotation convention. */
class EuclidTest {
    private static void canonical(int k, int n, String expected) {
        boolean[] p = Euclid.pattern(k, n);
        assertEquals(expected, Euclid.toText(p), "E(" + k + "," + n + ")");
        assertEquals(k, Euclid.pulses(p));
        assertTrue(p.length == 0 || p[0] || k == 0, "canonical starts on a pulse");
    }

    private static void upToRotation(int k, int n, String published) {
        assertTrue(Euclid.isRotationOf(Euclid.pattern(k, n), Euclid.fromText(published)), "E(" + k + "," + n + ") ~ " + published);
    }

    @Test
    void requestedPatterns() {
        canonical(3, 8, "x..x..x.");          // tresillo
        canonical(5, 8, "x.xx.xx.");          // cinquillo
        canonical(7, 12, "x.xx.x.xx.x.");     // bembe bell (West African)
        canonical(4, 16, "x...x...x...x..."); // four-on-the-floor kick in 16ths
    }

    @Test
    void morePublishedPatternsUpToRotation() {
        upToRotation(2, 5, "x.x..");
        upToRotation(3, 4, "x.xx");
        upToRotation(3, 5, "x.x.x");
        upToRotation(3, 7, "x.x.x..");
        upToRotation(4, 7, "x.x.x.x");
        upToRotation(4, 9, "x.x.x.x..");
        upToRotation(5, 9, "x.x.x.x.x");
        upToRotation(5, 11, "x.x.x.x.x..");
        upToRotation(5, 12, "x..x.x..x.x.");
        upToRotation(5, 16, "x..x..x..x..x...");
        upToRotation(7, 16, "x..x.x.x..x.x.x.");
        upToRotation(9, 16, "x.xx.x.x.xx.x.x.");
        upToRotation(13, 24, "x.xx.x.x.x.x.xx.x.x.x.x.");
    }

    @Test
    void edgeCasesAndEvenness() {
        assertEquals("....", Euclid.toText(Euclid.pattern(0, 4)));
        assertEquals("xxxx", Euclid.toText(Euclid.pattern(4, 4)));
        assertEquals("x", Euclid.toText(Euclid.pattern(1, 1)));
        assertEquals("x.......", Euclid.toText(Euclid.pattern(1, 8)));
        // Maximally even: gaps between consecutive pulses differ by at most one step.
        for (int n = 1; n <= 32; n++) {
            for (int k = 1; k <= n; k++) {
                boolean[] p = Euclid.pattern(k, n);
                assertEquals(k, Euclid.pulses(p));
                int lo = Integer.MAX_VALUE;
                int hi = 0;
                int prev = -1;
                int first = -1;
                for (int i = 0; i < n; i++) {
                    if (p[i]) {
                        if (prev >= 0) {
                            lo = Math.min(lo, i - prev);
                            hi = Math.max(hi, i - prev);
                        } else {
                            first = i;
                        }
                        prev = i;
                    }
                }
                int wrap = n - prev + first;
                lo = Math.min(lo, wrap);
                hi = Math.max(hi, wrap);
                assertTrue(hi - lo <= 1, "E(" + k + "," + n + ") gaps " + lo + ".." + hi);
            }
        }
        assertThrows(IllegalArgumentException.class, () -> Euclid.pattern(5, 4));
        assertThrows(IllegalArgumentException.class, () -> Euclid.pattern(-1, 4));
        assertThrows(IllegalArgumentException.class, () -> Euclid.pattern(1, 0));
        assertThrows(IllegalArgumentException.class, () -> Euclid.pattern(1, 65));
    }

    @Test
    void rotationIsLeftAndModN() {
        boolean[] t = Euclid.pattern(3, 8);
        assertEquals("..x..x.x", Euclid.toText(Euclid.rotate(t, 1)));
        assertEquals("x.x..x..", Euclid.toText(Euclid.rotate(t, 6)));
        assertEquals("x.x..x..", Euclid.toText(Euclid.rotate(t, -2)));
        assertArrayEquals(t, Euclid.rotate(t, 8));
        assertTrue(Euclid.isRotationOf(Euclid.rotate(t, 3), t));
        assertFalse(Euclid.isRotationOf(Euclid.pattern(5, 8), t));
    }
}
