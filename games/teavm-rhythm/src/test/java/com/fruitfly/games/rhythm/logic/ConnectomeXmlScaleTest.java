package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * Large-file correctness for {@link ConnectomeXml}: a generated 20k-neuron
 * ring (the shape whose (pre, post) keys all but share a Long.hashCode and
 * made the browser load quadratic). Sizes and CSR contents only; no timing.
 */
class ConnectomeXmlScaleTest {
    private static final int N = 20000;
    private static final int OUT = 20;

    private static String ring(int n, String extra) {
        StringBuilder b = new StringBuilder(n * OUT * 70);
        b.append("<hemibrain>\n");
        for (int i = 0; i < n; i++) {
            b.append("<neuron id=\"n").append(i).append("\"/>\n");
        }
        for (int i = 0; i < n; i++) {
            for (int k = 1; k <= OUT; k++) {
                b.append("<connection from=\"n").append(i).append("\" to=\"n").append((i + k) % n)
                        .append("\" weight=\"").append(k).append("\" delayMs=\"").append(k % 10 + 1).append("\"/>\n");
            }
        }
        b.append(extra);
        b.append("</hemibrain>\n");
        return b.toString();
    }

    @Test
    void parsesTwentyThousandNeuronRingIntoExactCsr() {
        Circuit c = ConnectomeXml.parse(ring(N, ""));
        assertEquals(N, c.neuronCount());
        assertEquals(N * OUT, c.synapseCount());
        for (int i = 0; i < N; i++) {
            assertEquals(i * OUT, c.rowStart(i));
            assertEquals((i + 1) * OUT, c.rowEnd(i));
            for (int k = 1; k <= OUT; k++) {
                int s = c.rowStart(i) + k - 1;
                assertEquals((i + k) % N, c.target(s));
                assertEquals(k, c.weight(s));
                assertEquals(k % 10 + 1, c.delayMs(s));
            }
        }
        assertEquals(N - 1, c.indexOf("n" + (N - 1)));
    }

    @Test
    void duplicateAtTheEndOfALargeRingIsStillRejected() {
        String dup = "<connection from=\"n" + (N - 1) + "\" to=\"n0\" weight=\"1\"/>\n";
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class,
                () -> ConnectomeXml.parse(ring(N, dup)));
        assertEquals("duplicate connection n" + (N - 1) + " -> n0", e.getMessage());
    }

    @Test
    void firstBadConnectionInDocumentOrderWins() {
        String extra = "<connection from=\"n5\" to=\"n6\" weight=\"1\"/>\n"
                + "<connection from=\"n7\" to=\"n9\" weight=\"x\"/>\n";
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class,
                () -> ConnectomeXml.parse(ring(100, extra)));
        assertEquals("duplicate connection n5 -> n6", e.getMessage());
        String extra2 = "<connection from=\"n7\" to=\"n9\" weight=\"x\"/>\n"
                + "<connection from=\"n5\" to=\"n6\" weight=\"1\"/>\n";
        e = assertThrows(IllegalArgumentException.class, () -> ConnectomeXml.parse(ring(100, extra2)));
        assertEquals("connection #" + (100 * OUT) + " weight is not a number: 'x'", e.getMessage());
    }

    @Test
    void sourcesOutOfDocumentOrderKeepPerRowDocumentOrder() {
        Circuit c = ConnectomeXml.parse("<hemibrain><neuron id=\"a\"/><neuron id=\"b\"/><neuron id=\"c\"/>"
                + "<connection from=\"c\" to=\"a\" weight=\"1\"/>"
                + "<connection from=\"a\" to=\"c\" weight=\"2\"/>"
                + "<connection from=\"c\" to=\"b\" weight=\"3\"/>"
                + "<connection from=\"a\" to=\"b\" weight=\"4\"/>"
                + "</hemibrain>");
        assertEquals(0, c.rowStart(0));
        assertEquals(2, c.rowEnd(0));
        assertEquals(2, c.rowStart(1));
        assertEquals(2, c.rowEnd(1));
        assertEquals(4, c.rowEnd(2));
        double[] want = {2, 4, 1, 3};
        int[] tgt = {2, 1, 0, 1};
        for (int k = 0; k < 4; k++) {
            assertEquals(want[k], c.weight(k));
            assertEquals(tgt[k], c.target(k));
        }
    }

    @Test
    void pairSetHandlesKeysThatShareOneLongHashCode() {
        // (i, i ^ 0x55) all have Long.hashCode == 0x55.
        int m = 100000;
        ConnectomeXml.PairSet set = new ConnectomeXml.PairSet(m);
        for (int i = 0; i < m; i++) {
            assertTrue(set.add(i, i ^ 0x55));
        }
        for (int i = 0; i < m; i++) {
            assertFalse(set.add(i, i ^ 0x55));
        }
        assertTrue(set.add(0, 0));
        assertFalse(set.add(0, 0));
    }
}
