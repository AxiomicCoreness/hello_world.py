package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

class NeuronSnapshotTest {
    private static final String[] LABELS = {"A", "B", "C", "D"};

    @Test
    void serializerShapeIsStableAndExact() {
        SpikeWindow w = new SpikeWindow(4);
        w.record(0, 100);   // outside the 2000 ms window ending at 3000
        w.record(0, 1500);
        w.record(0, 2900);
        w.record(2, 2999);
        List<NeuronSnapshot.Top> top = new ArrayList<>();
        top.add(new NeuronSnapshot.Top("lane0", "A", 3, 100));
        top.add(new NeuronSnapshot.Top("lane2", null, 1, 1));
        String json = NeuronSnapshot.build("lif", "lif", 3010, 3000, w,
                new double[] {-51.84, -52.0, -45.06, Double.NaN}, LABELS, 4, top);
        assertEquals("{\"v\":1,\"mode\":\"lif\",\"brain\":\"lif\",\"song_ms\":3010,\"brain_ms\":3000,"
                + "\"window_ms\":2000,\"window_end_ms\":3000,\"window_anchor\":\"brain\",\"lanes\":["
                + "{\"lane\":0,\"label\":\"A\",\"spikes\":2,\"rate_hz\":1.0,\"last_ms\":2900,\"v_mv\":-51.8,\"total\":3},"
                + "{\"lane\":1,\"label\":\"B\",\"spikes\":0,\"rate_hz\":0.0,\"last_ms\":null,\"v_mv\":-52.0,\"total\":0},"
                + "{\"lane\":2,\"label\":\"C\",\"spikes\":1,\"rate_hz\":0.5,\"last_ms\":2999,\"v_mv\":-45.1,\"total\":1},"
                + "{\"lane\":3,\"label\":\"D\",\"spikes\":0,\"rate_hz\":0.0,\"last_ms\":null,\"v_mv\":null,\"total\":0}],"
                + "\"total_spikes\":4,\"top\":["
                + "{\"id\":\"lane2\",\"region\":null,\"spikes\":1,\"ms_since\":1},"
                + "{\"id\":\"lane0\",\"region\":\"A\",\"spikes\":3,\"ms_since\":100}]}", json);
    }

    @Test
    void idleSnapshotCarriesNoLanes() {
        assertEquals("{\"v\":1,\"mode\":\"off\",\"brain\":\"idle\",\"song_ms\":0,\"window_ms\":2000,"
                + "\"lanes\":[],\"total_spikes\":0,\"top\":[]}", NeuronSnapshot.idle("off", 0));
    }

    @Test
    void jsonEscapesLabels() {
        assertEquals("\"a\\\"b\\\\c\\nd\\u0001\"", Json.str("a\"b\\c\nd\u0001"));
        assertEquals("-0.5", Json.num1(-0.46));
        assertEquals("12.3", Json.num1(12.34));
    }

    @Test
    void spikeWindowRingKeepsNewest() {
        SpikeWindow w = new SpikeWindow(1);
        for (int i = 0; i < SpikeWindow.CAPACITY + 10; i++) {
            w.record(0, i);
        }
        assertEquals(SpikeWindow.CAPACITY + 10, w.total(0));
        assertEquals(SpikeWindow.CAPACITY + 9, w.lastSpikeMs(0));
        assertEquals(SpikeWindow.CAPACITY, w.countInWindow(0, 1000, 2000));
        assertEquals(5, w.countInWindow(0, SpikeWindow.CAPACITY + 9, 5));
    }

    @Test
    void lifSnapshotReflectsRealSpikes() {
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        LifAutoplayer p = new LifAutoplayer(g);
        p.advanceTo(8000);
        long inWindow = 0;
        long total = 0;
        for (int l = 0; l < RhythmGame.LANES; l++) {
            total += p.spikeWindow().total(l);
            inWindow += p.spikeWindow().countInWindow(l, p.brainTimeMs(), NeuronSnapshot.WINDOW_MS);
        }
        assertEquals(p.spikeCount(), total, "window sees every autoplayer spike");
        assertTrue(inWindow > 0, "song is playing, lanes spiked in the last 2 s");
        String json = NeuronSnapshot.fromLif("lif", 8000, p, LABELS);
        assertTrue(json.startsWith("{\"v\":1,\"mode\":\"lif\",\"brain\":\"lif\",\"song_ms\":8000,\"brain_ms\":"));
        assertTrue(json.contains("\"total_spikes\":" + p.spikeCount()));
        assertFalse(json.contains("\n"));
    }

    @Test
    void connectomeSnapshotListsCircuitNeurons() {
        Circuit toy = ConnectomeXml.parse(ToyCircuitXml.XML);
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        ConnectomeAutoplayer p = new ConnectomeAutoplayer(g, toy);
        p.advanceTo(8000);
        long presses = 0;
        for (int l = 0; l < RhythmGame.LANES; l++) {
            presses += p.spikeWindow().total(l);
        }
        assertEquals(p.pressCount(), presses, "lane window = laneN.out spikes = presses");
        String json = NeuronSnapshot.fromConnectome("connectome", 8000, p, LABELS);
        assertTrue(json.contains("\"brain\":\"connectome\""));
        assertTrue(json.contains("\"top\":[{\"id\":\""), json);
    }

    /**
     * The HUD-side counter: every lane spike the autoplayer turns into a press,
     * recorded at the press sink with its substep time, then passed on to the game.
     */
    private static final class HudSink implements PressSink {
        final RhythmGame game;
        final List<long[]> spikes = new ArrayList<>();

        HudSink(RhythmGame game) {
            this.game = game;
        }

        @Override
        public void press(int lane, long timeMs) {
            spikes.add(new long[] {lane, timeMs});
            game.press(lane, timeMs, true);
        }

        long inWindow(long endMs) {
            long n = 0;
            for (long[] s : spikes) {
                if (s[1] > endMs - NeuronSnapshot.WINDOW_MS && s[1] <= endMs) {
                    n++;
                }
            }
            return n;
        }
    }

    private static String lanesJson(String json) {
        int a = json.indexOf("\"lanes\":[");
        int b = json.indexOf("],\"total_spikes\"");
        assertTrue(a >= 0 && b > a, json);
        return json.substring(a, b);
    }

    private static long sum(String json, String key) {
        Matcher m = Pattern.compile("\"" + key + "\":(\\d+)").matcher(json);
        long n = 0;
        while (m.find()) {
            n += Long.parseLong(m.group(1));
        }
        return n;
    }

    private static long jsonLong(String json, String key) {
        Matcher m = Pattern.compile("\"" + key + "\":(-?\\d+)").matcher(json);
        if (!m.find()) {
            fail("no \"" + key + "\" in " + json);
        }
        return Long.parseLong(m.group(1));
    }

    @Test
    void lifSnapshotLaneSpikesMatchHudCounterMidSong() {
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        HudSink hud = new HudSink(g);
        LifAutoplayer p = new LifAutoplayer(g, 0, hud);
        p.advanceTo(8000);
        assertEquals(p.spikeCount(), hud.spikes.size(), "HUD counter = every lane spike");
        String json = NeuronSnapshot.fromLif("lif", 8000, p, LABELS);
        long lanes = sum(lanesJson(json), "spikes");
        assertTrue(lanes > 0, json);
        assertEquals(p.brainTimeMs(), jsonLong(json, "window_end_ms"), "cues pending: window ends at brain time");
        assertTrue(json.contains("\"window_anchor\":\"brain\""), json);
        assertEquals(hud.inWindow(p.brainTimeMs()), lanes);
        assertEquals(p.spikeCount(), sum(lanesJson(json), "total"));
    }

    /**
     * Regression (live Chrome, PR #132): HUD said 57 spikes but /llm sent every
     * lane = 0, because the brain coasted seconds past the last note (long frame
     * after the final cue) and the window was anchored at brain time.
     */
    @Test
    void lifSnapshotKeepsSongSpikesWhenBrainCoastsPastLastNote() {
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        HudSink hud = new HudSink(g);
        LifAutoplayer p = new LifAutoplayer(g, 0, hud);
        long lastNote = g.chart().lastNoteMs();
        p.advanceTo(lastNote + 500);   // song plays out
        p.advanceTo(lastNote + 6000);  // one long frame: stalled or throttled tab
        assertTrue(g.isFinished());
        assertEquals(p.spikeCount(), hud.spikes.size(), "HUD counter = every lane spike");
        String json = NeuronSnapshot.fromLif("lif", lastNote + 6000, p, LABELS);
        long lanes = sum(lanesJson(json), "spikes");
        assertTrue(lanes > 0, "lanes must carry the song's real spikes, not 0: " + json);
        long end = jsonLong(json, "window_end_ms");
        assertEquals(hud.inWindow(end), lanes, "window counts = HUD-side spikes in the same window");
        assertTrue(end <= p.brainTimeMs());
        assertTrue(json.contains("\"window_anchor\":\"last_spike\""), json);
        assertEquals(p.brainTimeMs(), jsonLong(json, "brain_ms"), "brain clock still reported as is");
        assertEquals(p.spikeCount(), sum(lanesJson(json), "total"));
        assertEquals(p.spikeCount(), jsonLong(json, "total_spikes"));
    }

    @Test
    void connectomeSnapshotKeepsSongSpikesWhenBrainCoastsPastLastNote() {
        Circuit toy = ConnectomeXml.parse(ToyCircuitXml.XML);
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        HudSink hud = new HudSink(g);
        ConnectomeAutoplayer p = new ConnectomeAutoplayer(g, toy, 0, hud);
        long lastNote = g.chart().lastNoteMs();
        p.advanceTo(lastNote + 6000);
        assertEquals(p.pressCount(), hud.spikes.size(), "HUD keys = laneN.out spikes");
        String json = NeuronSnapshot.fromConnectome("connectome", lastNote + 6000, p, LABELS);
        long lanes = sum(lanesJson(json), "spikes");
        assertTrue(lanes > 0, json);
        assertEquals(hud.inWindow(jsonLong(json, "window_end_ms")), lanes);
        assertEquals(p.pressCount(), sum(lanesJson(json), "total"));
        assertEquals(p.spikeCount(), jsonLong(json, "total_spikes"));
        assertTrue(json.contains("\"top\":[{\"id\":\""), "circuit neurons active in the window: " + json);
    }

    @Test
    void windowEndOnlyMovesAfterLastCue() {
        SpikeWindow w = new SpikeWindow(2);
        assertEquals(9000, NeuronSnapshot.windowEndMs(9000, w, true), "never spiked: brain clock");
        w.record(1, 4000);
        w.record(0, 4200);
        assertEquals(4200, w.latestSpikeMs());
        assertEquals(9000, NeuronSnapshot.windowEndMs(9000, w, false), "cues pending: brain clock");
        assertEquals(4200, NeuronSnapshot.windowEndMs(9000, w, true), "cues done: newest real spike");
    }
}
