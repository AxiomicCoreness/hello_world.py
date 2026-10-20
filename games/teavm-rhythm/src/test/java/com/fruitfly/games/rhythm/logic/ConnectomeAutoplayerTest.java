package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Paths;
import org.junit.jupiter.api.Test;

class ConnectomeAutoplayerTest {
    private static final Circuit TOY = ConnectomeXml.parse(ToyCircuitXml.XML);

    /** [score, perfect, great, good, miss, presses, spikes, maxCombo]. */
    private static long[] play(NoteChart chart, long frameMs) {
        RhythmGame g = new RhythmGame(chart);
        ConnectomeAutoplayer p = new ConnectomeAutoplayer(g, TOY);
        long end = g.chart().lastNoteMs() + 1000;
        for (long t = 0; t <= end; t += frameMs) {
            p.advanceTo(t);
            g.update(t);
        }
        p.advanceTo(end);
        g.update(end);
        assertTrue(g.isFinished());
        return new long[] {g.score(), g.perfectCount(), g.greatCount(), g.goodCount(), g.missCount(),
            p.pressCount(), p.spikeCount(), g.maxCombo()};
    }

    private static NoteChart sample() throws Exception {
        return ChartJson.parse(Files.readString(Paths.get("src/main/webapp/charts/sample_chart.json"))).chart();
    }

    @Test
    void latencyIsMeasuredThroughTheCircuit() {
        // in spikes 3 ms after the cue; +1+2 ms to inter, which spikes 3 ms later; +1+2 to out, +3.
        for (int l = 0; l < 4; l++) {
            assertEquals(15, ConnectomeAutoplayer.measureLatencyMs(TOY, l), "lane " + l);
        }
    }

    @Test
    void sampleChartAllPerfect() throws Exception {
        long[] r = play(sample(), 16);
        assertEquals(6, r[1], "PERFECT");
        assertEquals(0, r[4], "MISS");
        assertEquals(1800, r[0]);
        assertEquals(6, r[5], "one press per note");
        assertEquals(18, r[6], "3 spikes per note (in, inter, out)");
    }

    @Test
    void seed2026HitRate() {
        long[] r = play(NoteChart.generate(2026, 64, 120, 2000), 16);
        assertEquals(64, r[1] + r[2] + r[3], "hits");
        assertEquals(64, r[1], "PERFECT");
        assertEquals(0, r[4]);
        assertEquals(58_800, r[0]);
        assertEquals(64, r[5]);
        assertEquals(64, r[7]);
    }

    @Test
    void deterministicAcrossRunsAndFrameRates() throws Exception {
        for (NoteChart c : new NoteChart[] {sample(), NoteChart.generate(2026, 64, 120, 2000)}) {
            long[] a = play(c.fresh(), 16);
            long[] b = play(c.fresh(), 16);
            long[] d = play(c.fresh(), 7);
            long[] e = play(c.fresh(), 1000);
            for (int i = 0; i < a.length; i++) {
                assertEquals(a[i], b[i], "repeat, field " + i);
                assertEquals(a[i], d[i], "7 ms frames, field " + i);
                assertEquals(a[i], e[i], "1 s frames, field " + i);
            }
        }
    }

    @Test
    void otherSeedsMostlyHit() {
        for (long seed : new long[] {1, 7, 42, 99, 123456789L}) {
            long[] r = play(NoteChart.generate(seed, 64, 120, 2000), 16);
            assertTrue(r[1] + r[2] + r[3] >= 58, "seed " + seed + " hit " + (r[1] + r[2] + r[3]));
        }
    }

    @Test
    void cutOutputMeansNoPresses() {
        // Remove lane 1's inter -> out synapse: lane 1 notes can't be pressed, others still are.
        String cut = ToyCircuitXml.XML.replace(
                "<connection from=\"lane1.inter\" to=\"lane1.out\" weight=\"60\" delayMs=\"2\"/>", "");
        Circuit c = ConnectomeXml.parse(cut);
        assertThrows(IllegalArgumentException.class, () -> ConnectomeAutoplayer.measureLatencyMs(c, 1));
        assertEquals(15, ConnectomeAutoplayer.measureLatencyMs(c, 0));
    }

    @Test
    void missingLaneNeuronRejected() {
        Circuit c = ConnectomeXml.parse("<hemibrain><neuron id='A'/></hemibrain>");
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class,
                () -> new ConnectomeAutoplayer(new RhythmGame(NoteChart.generate(1, 4, 120, 2000)), c));
        assertEquals("connectome has no input neuron 'lane0.in'", e.getMessage());
    }
}
