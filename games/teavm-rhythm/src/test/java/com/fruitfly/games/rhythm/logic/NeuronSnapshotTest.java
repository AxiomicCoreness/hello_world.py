package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
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
                + "\"window_ms\":2000,\"lanes\":["
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
}
