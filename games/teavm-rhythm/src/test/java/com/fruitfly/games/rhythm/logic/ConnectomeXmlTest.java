package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import org.junit.jupiter.api.Test;

/** ConnectomeXml mirrors com.fruitfly.brain.ConnectomeLoader's rules and the (stricter) connectome.xsd. */
class ConnectomeXmlTest {
    private static final String AB = "<hemibrain><neuron id='A'/><neuron id='B'/>";

    private static int[] targets(Circuit c, int pre) {
        int[] out = new int[c.rowEnd(pre) - c.rowStart(pre)];
        for (int k = c.rowStart(pre); k < c.rowEnd(pre); k++) {
            out[k - c.rowStart(pre)] = c.target(k);
        }
        return out;
    }

    @Test
    void toyCircuitParses() {
        Circuit c = ConnectomeXml.parse(ToyCircuitXml.XML);
        assertEquals(12, c.neuronCount());
        assertEquals(20, c.synapseCount());
        String[] regions = {"antennal lobe", "mushroom body", "lateral horn", "lobula"};
        for (int l = 0; l < 4; l++) {
            assertEquals(regions[l], c.region(c.indexOf("lane" + l + ".out")));
            assertEquals(regions[l], ConnectomeAutoplayer.laneLabel(c, l));
        }
        int out0 = c.indexOf("lane0.out");
        assertArrayEquals(new int[] {c.indexOf("lane1.inter"), c.indexOf("lane2.inter"), c.indexOf("lane3.inter")},
                targets(c, out0));
        for (int k = c.rowStart(out0); k < c.rowEnd(out0); k++) {
            assertEquals(-15.0, c.weight(k));
            assertEquals(2.0, c.delayMs(k));
            assertEquals(out0, c.source(k));
        }
    }

    @Test
    void rootPlaceholderRingParses() throws IOException {
        // The repo's only connectome data: a hand-written 3-neuron PLACEHOLDER, not FlyEM data.
        Circuit c = ConnectomeXml.parse(Files.readString(Paths.get("../../src/main/resources/HHMIJaneliaMap.xml")));
        assertEquals(3, c.neuronCount());
        assertEquals(3, c.synapseCount());
        assertArrayEquals(new int[] {1}, targets(c, 0));
        assertEquals(0.8, c.weight(c.rowStart(1)));
        assertEquals(ConnectomeXml.DEFAULT_DELAY_MS, c.delayMs(0));
        assertNull(c.region(0));
    }

    @Test
    void loaderSemantics() {
        Circuit c = ConnectomeXml.parse("<hemibrain><connection from='B' to='A' weight='1'/>"
                + "<neuron id=' A '/><neuron id='B'/><connection from='A' to='A' weight='-2.5' delayMs='60'/>"
                + "<connection from='A' to='B' weight='+.5' delayMs='5.'/></hemibrain>");
        assertEquals(0, c.indexOf("A")); // trimmed, document order
        assertArrayEquals(new int[] {0, 1}, targets(c, 0)); // self-loop allowed, document order within row
        assertEquals(-2.5, c.weight(0));
        assertEquals(60.0, c.delayMs(0));
        assertEquals(0.5, c.weight(1));
        assertEquals(5.0, c.delayMs(1));
        assertArrayEquals(new int[] {0}, targets(c, 1));
        assertEquals(1.0, c.delayMs(2));
    }

    @Test
    void xmlSurfaceAccepted() {
        ConnectomeXml.parse("<hemibrain/>");
        ConnectomeXml.parse("\uFEFF<?xml version='1.0'?>\n<!-- c --><hemibrain>\n <!-- x --><?pi y?>"
                + "<neuron id=\"a&amp;b\"></neuron><neuron id='&#931;'/></hemibrain>\n<!-- end -->\n");
        Circuit c = ConnectomeXml.parse("<hemibrain xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'"
                + " xsi:noNamespaceSchemaLocation='connectome.xsd'><neuron id='a&amp;b'/><neuron id='&#x3A3;'/>"
                + "<connection from='a&amp;b' to='&#931;' weight='1E3' delayMs=' 2.5 '/></hemibrain>");
        assertEquals(1000.0, c.weight(0));
        assertEquals(2.5, c.delayMs(0));
    }

    @Test
    void rejections() {
        String[] bad = {
            "", "not xml", "<hemibrain>", "<other/>", "<hemibrain/><hemibrain/>",
            "<!DOCTYPE hemibrain [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><hemibrain/>",
            "<hemibrain><![CDATA[x]]></hemibrain>",
            "<hemibrain>hello</hemibrain>",
            "<hemibrain><meta/></hemibrain>",
            "<hemibrain><neuron id='A' type='KC'/></hemibrain>",
            "<hemibrain><neuron id='A'><neuron id='B'/></neuron></hemibrain>",
            "<hemibrain><neuron id=A/></hemibrain>",
            "<hemibrain><neuron/></hemibrain>",
            "<hemibrain><neuron id='  '/></hemibrain>",
            "<hemibrain><neuron id='A' region=' '/></hemibrain>",
            "<hemibrain><neuron id='A'/><neuron id='A'/></hemibrain>",
            AB + "<connection from='A' to='C' weight='1'/></hemibrain>",
            AB + "<connection from='C' to='A' weight='1'/></hemibrain>",
            AB + "<connection from='A' to='B'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1'/><connection from='A' to='B' weight='2'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1d'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='0x1p3'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='NaN'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='INF'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1e999'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1' delayMs='0'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1' delayMs='-1'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1' region='x'/></hemibrain>",
            AB + "<connection from='A' to='B' weight='1' weight='2'/></hemibrain>",
            "<hemibrain xmlns='urn:x'/>",
        };
        for (String xml : bad) {
            assertThrows(IllegalArgumentException.class, () -> ConnectomeXml.parse(xml), xml);
        }
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class,
                () -> ConnectomeXml.parse(AB + "<connection from='A' to='Z' weight='1'/></hemibrain>"));
        assertEquals("connection #0 references unknown target neuron 'Z'", e.getMessage());
        e = assertThrows(IllegalArgumentException.class, () -> ConnectomeXml.parse("<hemibrain>\n<meta/></hemibrain>"));
        assertEquals("connectome line 2: unknown element <meta>", e.getMessage());
    }

    @Test
    void decimalLexicalForm() {
        for (String ok : new String[] {"1", "-0", "+.5", "5.", "1E3", "2.5e-3", "007"}) {
            assertTrue(ConnectomeXml.isDecimal(ok), ok);
        }
        for (String no : new String[] {"", ".", "+", "1e", "1d", "0x10", "1.2.3", "e5", "INF", "1 2"}) {
            assertTrue(!ConnectomeXml.isDecimal(no), no);
        }
    }
}
