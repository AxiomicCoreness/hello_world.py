package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import org.junit.jupiter.api.Test;

/** The README and page examples are what the implementation actually produces. */
class EuclidDocsTest {
    private static String readme() throws Exception {
        return Files.readString(Paths.get("README.md"));
    }

    private static String page() throws Exception {
        return Files.readString(Paths.get("src/main/webapp/index.html"));
    }

    @Test
    void foldTraceForE38MatchesTheDocs() throws Exception {
        List<String> t = Euclid.foldTrace(3, 8);
        assertEquals(List.of("[1][1][1][0][0][0][0][0]", "[1,0][1,0][1,0][0][0]", "[1,0,0][1,0,0][1,0]", "10010010"), t);
        String r = readme();
        assertTrue(r.contains(String.join("\n", t)), "README shows the exact trace");
        assertTrue(page().contains("[1,0][1,0][1,0][0][0] \\to [1,0,0][1,0,0][1,0] \\to 10010010"), "page KaTeX shows it");
    }

    @Test
    void floorFormulaEqualsBjorklundUpToRotation() throws Exception {
        assertEquals("x.x..x..", Euclid.toText(Euclid.floorPattern(3, 8)));
        assertTrue(readme().contains("P = 0, 2, 5, i.e. `x.x..x..`"));
        for (int n = 1; n <= 24; n++) {
            for (int k = 1; k <= n; k++) {
                assertTrue(Euclid.isRotationOf(Euclid.floorPattern(k, n), Euclid.pattern(k, n)), "E(" + k + "," + n + ")");
            }
        }
    }

    @Test
    void bembeGapsAreMajorScaleStepsUpToRotation() throws Exception {
        boolean[] b = Euclid.pattern(7, 12);
        assertEquals("101101011010", Euclid.toText(b).replace('x', '1').replace('.', '0'));
        assertArrayEquals(new int[] {2, 1, 2, 2, 1, 2, 2}, Euclid.gaps(b));
        int[] major = {2, 2, 1, 2, 2, 2, 1};
        boolean found = false;
        for (int r = 0; r < 7; r++) {
            boolean ok = true;
            for (int i = 0; i < 7; i++) {
                ok &= Euclid.gaps(b)[(i + r) % 7] == major[i];
            }
            found |= ok;
        }
        assertTrue(found);
        assertTrue(readme().contains("E(7,12), the bembe bell, is `101101011010`: onset gaps 2,1,2,2,1,2,2"));
        assertTrue(page().contains("E(7,12) = 101101011010,\\quad \\text{gaps } 2,2,1,2,2,2,1"));
    }

    @Test
    void presetTableMatchesTheImplementation() throws Exception {
        String r = readme();
        String p = page();
        for (EuclidSong.Preset preset : EuclidSong.PRESETS) {
            if (preset.layers().length != 1) {
                continue;
            }
            EuclidSong.Layer l = preset.layers()[0];
            String row = "| " + RhythmGame.LANE_KEYS[l.lane] + " | " + l.name + " " + l.formula() + " | `" + l.text() + "` |";
            assertTrue(r.contains(row), row);
            assertTrue(p.contains(l.formula() + " <code>" + l.text() + "</code>") || p.contains(l.formula() + "\n      <code>" + l.text() + "</code>"),
                "page lists " + l.formula());
        }
        // Integration note: 12 neurons, 20 synapses in the toy circuit, as documented.
        Circuit toy = ConnectomeXml.parse(ToyCircuitXml.XML);
        assertEquals(12, toy.neuronCount());
        assertEquals(20, toy.synapseCount());
        assertTrue(r.contains("12-neuron, 20-synapse TOY circuit") && p.contains("12-neuron, 20-synapse TOY circuit"));
    }
}
