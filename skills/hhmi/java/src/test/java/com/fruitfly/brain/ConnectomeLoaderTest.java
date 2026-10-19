package com.fruitfly.brain;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

class ConnectomeLoaderTest {

    private static final String RESOURCE = "HHMIJaneliaMap.xml";

    private static Connectome fromString(String xml) throws IOException {
        return ConnectomeLoader.load(
                new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)), "test");
    }

    @Test
    void janeliaMapResourceIsPresent() {
        assertNotNull(ConnectomeLoaderTest.class.getClassLoader().getResource(RESOURCE));
    }

    @Test
    void placeholderLoadsAsThreeNeuronRing() throws IOException {
        Connectome c = ConnectomeLoader.loadFromResource(RESOURCE);
        assertEquals(3, c.neuronCount());
        assertEquals(3, c.synapseCount());
        // A=0 -> B=1 (1.0), B=1 -> C=2 (0.8), C=2 -> A=0 (0.5)
        assertArrayEquals(new int[] {1}, c.postsynaptic(0));
        assertArrayEquals(new int[] {2}, c.postsynaptic(1));
        assertArrayEquals(new int[] {0}, c.postsynaptic(2));
        assertArrayEquals(new double[] {1.0}, c.weightsOf(0), 0.0);
        assertArrayEquals(new double[] {0.8}, c.weightsOf(1), 0.0);
        assertArrayEquals(new double[] {0.5}, c.weightsOf(2), 0.0);
        for (int i = 0; i < 3; i++) {
            assertArrayEquals(new double[] {ConnectomeLoader.DEFAULT_DELAY_MS}, c.delaysOf(i), 0.0);
        }
    }

    @Test
    void loadFromXmlPathMatchesResource(@TempDir Path dir) throws IOException {
        Path f = dir.resolve("m.xml");
        try (var in = getClass().getClassLoader().getResourceAsStream(RESOURCE)) {
            Files.copy(in, f);
        }
        Connectome c = ConnectomeLoader.loadFromXml(f);
        assertEquals(3, c.neuronCount());
        assertEquals(3, c.synapseCount());
    }

    @Test
    void rowsAreSortedBySourceAndDelayIsParsed() throws IOException {
        Connectome c = fromString("<hemibrain><neuron id='x'/><neuron id='y'/><neuron id='z'/>"
                + "<connection from='z' to='x' weight='-0.25' delayMs='3.5'/>"
                + "<connection from='x' to='z' weight='0.1'/>"
                + "<connection from='x' to='y' weight='0.2'/>"
                + "<connection from='y' to='y' weight='0.3'/></hemibrain>");
        assertArrayEquals(new int[] {2, 1}, c.postsynaptic(0));
        assertArrayEquals(new double[] {0.1, 0.2}, c.weightsOf(0), 0.0);
        assertArrayEquals(new int[] {1}, c.postsynaptic(1)); // self-loop allowed
        assertArrayEquals(new int[] {0}, c.postsynaptic(2));
        assertArrayEquals(new double[] {-0.25}, c.weightsOf(2), 0.0);
        assertArrayEquals(new double[] {3.5}, c.delaysOf(2), 0.0);
    }

    @Test
    void duplicateNeuronIdRejected() {
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () ->
                fromString("<hemibrain><neuron id='A'/><neuron id='A'/></hemibrain>"));
        assertTrue(e.getMessage().contains("duplicate neuron id 'A'"), e.getMessage());
    }

    @Test
    void unknownTargetRejected() {
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () ->
                fromString("<hemibrain><neuron id='A'/>"
                        + "<connection from='A' to='Q' weight='1'/></hemibrain>"));
        assertTrue(e.getMessage().contains("unknown target neuron 'Q'"), e.getMessage());
    }

    @Test
    void badNumbersRejected() {
        String pre = "<hemibrain><neuron id='A'/><neuron id='B'/>";
        assertThrows(IllegalArgumentException.class, () ->
                fromString(pre + "<connection from='A' to='B' weight='NaN'/></hemibrain>"));
        assertThrows(IllegalArgumentException.class, () ->
                fromString(pre + "<connection from='A' to='B' weight='Infinity'/></hemibrain>"));
        assertThrows(IllegalArgumentException.class, () ->
                fromString(pre + "<connection from='A' to='B'/></hemibrain>"));
        assertThrows(IllegalArgumentException.class, () ->
                fromString(pre + "<connection from='A' to='B' weight='1' delayMs='0'/></hemibrain>"));
        assertThrows(IllegalArgumentException.class, () ->
                fromString(pre + "<connection from='A' to='B' weight='1'/>"
                        + "<connection from='A' to='B' weight='2'/></hemibrain>"));
    }

    @Test
    void doctypeAndXxeRejected(@TempDir Path dir) throws IOException {
        Path secret = dir.resolve("secret.txt");
        Files.writeString(secret, "TOPSECRET");
        String xxe = "<?xml version='1.0'?>\n"
                + "<!DOCTYPE hemibrain [<!ENTITY xxe SYSTEM '" + secret.toUri() + "'>]>\n"
                + "<hemibrain><neuron id='&xxe;'/></hemibrain>";
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () -> fromString(xxe));
        assertTrue(e.getMessage().contains("DOCTYPE"), e.getMessage());
        assertFalse(e.getMessage().contains("TOPSECRET"));
    }

    @Test
    void missingFileAndResourceRejected(@TempDir Path dir) {
        assertThrows(IllegalArgumentException.class, () ->
                ConnectomeLoader.loadFromXml(dir.resolve("nope.xml")));
        assertThrows(IllegalArgumentException.class, () ->
                ConnectomeLoader.loadFromResource("does-not-exist.xml"));
    }

    @Test
    void wrongRootRejected() {
        assertThrows(IllegalArgumentException.class, () -> fromString("<brain/>"));
    }

    @Test
    void automatonAcceptsLoadedConnectome() throws IOException {
        Connectome c = ConnectomeLoader.loadFromResource(RESOURCE);
        SovereignAutomaton a = new SovereignAutomaton(c, c.neuronCount());
        assertEquals(3, a.swarm().size());
        assertThrows(IllegalArgumentException.class, () -> new SovereignAutomaton(c, 8));
        String reply = a.respond("hi", 0.0, 0.0);
        assertFalse(reply.isEmpty());
        for (int k = 0; k < 10; k++) {
            a.step(1e-4, 0.5);
        }
    }
}
