package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;

class ChartJsonTest {
    private static final String META =
            "\"metadata\":{\"title\":\"T\",\"artist\":\"A\",\"bpm\":120,\"offset_ms\":0}";

    private static String chart(String notes) {
        return "{" + META + ",\"notes\":[" + notes + "]}";
    }

    private static String error(String json) {
        return assertThrows(ChartFormatException.class, () -> ChartJson.parse(json)).getMessage();
    }

    @Test
    void sampleChartFileParses() throws IOException {
        String text = Files.readString(Paths.get("src/main/webapp/charts/sample_chart.json"));
        LoadedChart c = ChartJson.parse(text);
        assertEquals("Fruit Fly Heartbeat", c.title());
        assertEquals("LIF Autoplayer", c.artist());
        assertEquals(120.0, c.bpm());
        assertEquals(0L, c.offsetMs());
        assertNull(c.audio());
        List<Note> n = c.chart().notes();
        long[][] want = {{1000, 0}, {1500, 0}, {2000, 2}, {2000, 3}, {2500, 1}, {3000, 1}};
        assertEquals(want.length, n.size());
        for (int i = 0; i < want.length; i++) {
            assertEquals(want[i][0], n.get(i).timeMs(), "time " + i);
            assertEquals(want[i][1], n.get(i).lane(), "lane " + i);
            assertFalse(n.get(i).isResolved());
        }
        assertEquals(-1L, c.chart().seed());
        assertEquals(3000L, c.chart().lastNoteMs());
    }

    @Test
    void sampleChartPlaysThroughExistingEngine() throws IOException {
        LoadedChart c = ChartJson.parse(Files.readString(Paths.get("src/main/webapp/charts/sample_chart.json")));
        RhythmGame g = new RhythmGame(c.chart().fresh());
        assertEquals(Judgement.PERFECT, g.press(0, 1000));
        assertEquals(Judgement.GREAT, g.press(0, 1560));
        assertEquals(Judgement.PERFECT, g.press(3, 2000)); // simultaneous notes judged per lane
        assertEquals(Judgement.GOOD, g.press(2, 2120));
        g.update(3200);                                      // 2500 and 3000 in lane 1 lapse
        assertTrue(g.isFinished());
        assertEquals(300 + 200 + 300 + 100, g.score());
        assertEquals(2, g.missCount());
    }

    @Test
    void autoplayerPlaysSampleChart() throws IOException {
        LoadedChart c = ChartJson.parse(Files.readString(Paths.get("src/main/webapp/charts/sample_chart.json")));
        RhythmGame g = new RhythmGame(c.chart().fresh());
        LifAutoplayer brain = new LifAutoplayer(g);
        for (long t = 0; t <= 4000 && !g.isFinished(); t += 16) {
            brain.advanceTo(t);
            g.update(t);
        }
        assertTrue(g.isFinished());
        assertEquals(6, g.perfectCount());
        assertEquals(1800L, g.score());
        assertEquals(6, brain.spikeCount());
    }

    @Test
    void unsortedNotesAreStablySorted() {
        LoadedChart c = ChartJson.parse(chart(
                "{\"time_ms\":900,\"lane\":1},{\"time_ms\":100,\"lane\":3},{\"time_ms\":500,\"lane\":2},"
                        + "{\"time_ms\":100,\"lane\":0}"));
        List<Note> n = c.chart().notes();
        assertEquals(Arrays.asList(100L, 100L, 500L, 900L),
                Arrays.asList(n.get(0).timeMs(), n.get(1).timeMs(), n.get(2).timeMs(), n.get(3).timeMs()));
        assertEquals(3, n.get(0).lane()); // equal times keep input order
        assertEquals(0, n.get(1).lane());
    }

    @Test
    void optionalFieldsAndUnknownKeys() {
        LoadedChart c = ChartJson.parse("{\"metadata\":{\"title\":\"\\u00e9t\\u00e9 \\\"q\\\"\",\"artist\":\"B\","
                + "\"bpm\":97.5,\"offset_ms\":-40,\"audio\":\"song.ogg\",\"extra\":[1,{\"x\":null}]},"
                + "\"notes\":[{\"time_ms\":1.2e3,\"lane\":3,\"hold\":false}],\"v\":true}");
        assertEquals("\u00e9t\u00e9 \"q\"", c.title());
        assertEquals(97.5, c.bpm());
        assertEquals(-40L, c.offsetMs());
        assertEquals("song.ogg", c.audio());
        assertEquals(1200L, c.chart().notes().get(0).timeMs());
    }

    @Test
    void emptyNotesAllowed() {
        LoadedChart c = ChartJson.parse(chart(""));
        assertTrue(c.chart().notes().isEmpty());
        assertTrue(new RhythmGame(c.chart()).isFinished());
    }

    @Test
    void rejectsBadLane() {
        assertEquals("notes[1].lane: must be an integer 0..3, got 4",
                error(chart("{\"time_ms\":0,\"lane\":0},{\"time_ms\":10,\"lane\":4}")));
        assertEquals("notes[0].lane: must be an integer 0..3, got -1", error(chart("{\"time_ms\":0,\"lane\":-1}")));
        assertEquals("notes[0].lane: must be an integer 0..3, got 1.5", error(chart("{\"time_ms\":0,\"lane\":1.5}")));
        assertEquals("notes[0].lane: must be a number, got a string", error(chart("{\"time_ms\":0,\"lane\":\"1\"}")));
    }

    @Test
    void rejectsBadTime() {
        assertEquals("notes[0].time_ms: must be an integer in [0, 86400000], got -5",
                error(chart("{\"time_ms\":-5,\"lane\":0}")));
        assertEquals("notes[0].time_ms: must be an integer in [0, 86400000], got 10.5",
                error(chart("{\"time_ms\":10.5,\"lane\":0}")));
        assertEquals("notes[0]: missing \"time_ms\"", error(chart("{\"lane\":0}")));
        assertEquals("notes[0]: must be an object, got a number", error(chart("7")));
    }

    @Test
    void rejectsDuplicateLaneAndTime() {
        assertEquals("notes: duplicate note: lane 2 at 500 ms appears twice",
                error(chart("{\"time_ms\":500,\"lane\":2},{\"time_ms\":500,\"lane\":1},{\"time_ms\":500,\"lane\":2}")));
    }

    @Test
    void rejectsBadMetadata() {
        assertEquals("chart: missing \"metadata\"", error("{\"notes\":[]}"));
        assertEquals("chart: missing \"notes\"", error("{" + META + "}"));
        assertEquals("notes: must be an array, got an object", error("{" + META + ",\"notes\":{}}"));
        assertEquals("metadata: missing \"bpm\"",
                error("{\"metadata\":{\"title\":\"T\",\"artist\":\"A\",\"offset_ms\":0},\"notes\":[]}"));
        assertEquals("metadata.bpm: must be > 0 and <= 1000, got 0",
                error("{\"metadata\":{\"title\":\"T\",\"artist\":\"A\",\"bpm\":0,\"offset_ms\":0},\"notes\":[]}"));
        assertEquals("metadata.title: must be a string, got a number",
                error("{\"metadata\":{\"title\":1,\"artist\":\"A\",\"bpm\":60,\"offset_ms\":0},\"notes\":[]}"));
        assertEquals("metadata.offset_ms: must be an integer in [-600000, 600000], got 0.5",
                error("{\"metadata\":{\"title\":\"T\",\"artist\":\"A\",\"bpm\":60,\"offset_ms\":0.5},\"notes\":[]}"));
        assertEquals("chart: must be an object, got an array", error("[]"));
    }

    @Test
    void rejectsMalformedJson() {
        assertEquals("invalid JSON at line 1, column 3: empty document", error("  "));
        assertTrue(error("{\"metadata\":").startsWith("invalid JSON at line 1, column 13: unexpected end"));
        assertTrue(error("{\"a\":1,}").contains("expected a string key"));
        assertTrue(error("{\"a\":1}{").contains("unexpected trailing text"));
        assertTrue(error("{\"a\":01}").contains("expected ',' or '}'"));
        assertTrue(error("{\"a\":1.}").contains("digits expected after '.'"));
        assertTrue(error("{\"a\":tru}").contains("expected true"));
        assertTrue(error("{\"a\":\"x\ny\"}").contains("control character"));
        assertTrue(error("{\"a\":1,\"a\":2}").contains("duplicate key \"a\""));
        assertTrue(error("{\n  'a': 1\n}").startsWith("invalid JSON at line 2, column 3:"));
        assertTrue(error("{\"a\":1e999}").contains("number out of range"));
        StringBuilder deep = new StringBuilder();
        for (int i = 0; i < 70; i++) {
            deep.append('[');
        }
        assertTrue(error(deep.toString()).contains("nesting deeper than 64"));
        assertTrue(error(null).contains("null"));
    }

    @Test
    void fromNotesValidatesAndCopies() {
        Note a = new Note(1, 300);
        NoteChart c = NoteChart.fromNotes(Arrays.asList(a, new Note(0, 100)));
        assertEquals(100L, c.notes().get(0).timeMs());
        assertFalse(c.notes().contains(a)); // copied, so resolving the chart can't touch the input
        assertThrows(IllegalArgumentException.class, () -> NoteChart.fromNotes(null));
        assertThrows(IllegalArgumentException.class, () -> NoteChart.fromNotes(Arrays.asList(a, null)));
        assertThrows(UnsupportedOperationException.class, () -> c.notes().add(new Note(0, 1)));
    }
}
