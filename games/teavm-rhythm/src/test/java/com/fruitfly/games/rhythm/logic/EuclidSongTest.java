package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

/** Euclidean presets -> chart notes, lanes, HUD strings, audio, and every fly mode playing them. */
class EuclidSongTest {
    @Test
    void presetsIncludeTheRequiredPatternsOnTheirLanes() {
        String[][] want = {{"tresillo", "x..x..x.", "F"}, {"cinquillo", "x.xx.xx.", "J"},
            {"bembe", "x.xx.x.xx.x.", "K"}, {"kick", "x...x...x...x...", "D"}};
        for (String[] w : want) {
            EuclidSong.Preset p = EuclidSong.PRESETS[EuclidSong.indexOf(w[0])];
            assertEquals(1, p.layers().length);
            assertEquals(w[1], p.layers()[0].text());
            assertEquals(w[2], RhythmGame.LANE_KEYS[p.layers()[0].lane]);
        }
        EuclidSong.Preset layered = EuclidSong.PRESETS[0];
        assertEquals("layered", layered.id);
        assertEquals(List.of("D E(4,16) x...x...x...x...", "F E(3,8) x..x..x.", "J E(5,8) x.xx.xx.", "K E(7,12) x.xx.x.xx.x."),
            EuclidSong.hudLines(layered));
        assertEquals(-1, EuclidSong.indexOf("nope"));
    }

    @Test
    void everyPulseIsOneNoteOnTheBarGrid() {
        EuclidSong.Preset t = EuclidSong.PRESETS[EuclidSong.indexOf("tresillo")];
        List<Note> n = EuclidSong.notes(t, 120, 2);
        assertEquals(6, n.size());
        long[] at = {2000, 2750, 3500, 4000, 4750, 5500}; // bar 2000 ms, 8th = 250 ms: steps 0, 3, 6
        for (int i = 0; i < at.length; i++) {
            assertEquals(at[i], n.get(i).timeMs());
            assertEquals(1, n.get(i).lane());
        }
        // Bembe: 12 triplet-eighths per bar at 90 BPM (bar 2666.67 ms), rounded per step from the song start.
        assertEquals(2000 + Math.round(13 * 240000.0 / 90 / 12), EuclidSong.stepMs(1, 1, 12, 90));
        LoadedChart c = EuclidSong.chart(EuclidSong.PRESETS[0], 120);
        int perBar = 4 + 3 + 5 + 7;
        assertEquals(perBar * EuclidSong.BARS, c.chart().notes().size());
        assertEquals(0, c.offsetMs());
        assertTrue(c.title().contains("LAYERED"));
        for (int i = 1; i < c.chart().notes().size(); i++) {
            assertTrue(c.chart().notes().get(i).timeMs() >= c.chart().notes().get(i - 1).timeMs(), "sorted");
        }
        assertEquals("120 BPM", EuclidSong.bpmLabel(120));
    }

    @Test
    void everyFlyModePlaysEveryPresetAtEveryBpm() {
        for (EuclidSong.Preset p : EuclidSong.PRESETS) {
            for (int bpm : EuclidSong.BPMS) {
                NoteChart chart = EuclidSong.chart(p, bpm).chart();
                for (int mode : FlyPlay.MODES) {
                    long[] r = FlyPlay.play(chart, mode, 16);
                    String what = p.id + " @" + bpm + " mode " + mode + " P/Gr/Go/M " + r[1] + "/" + r[2] + "/" + r[3] + "/" + r[4];
                    assertEquals(0, r[4], what);
                    assertEquals(r[5], r[1] + r[2] + r[3], what);
                    if (!ControlMode.isAssist(mode)) {
                        assertEquals(r[5], r[1], "full autoplay is all PERFECT: " + what);
                    }
                }
            }
        }
    }

    @Test
    void audioHasDistinctTimbresAndHitsOnTheNotes() {
        int rate = EuclidTrack.SAMPLE_RATE;
        EuclidSong.Preset layered = EuclidSong.PRESETS[0];
        short[] pcm = EuclidTrack.samples(layered, 120, rate);
        long last = EuclidSong.chart(layered, 120).chart().lastNoteMs();
        assertEquals((int) ((last + 1500) * rate / 1000), pcm.length);
        // Silent lead-in, sound right at the first notes (2000 ms).
        for (int i = 0; i < EuclidTrack.onsetSample(1990, rate); i++) {
            assertEquals(0, pcm[i]);
        }
        int at = EuclidTrack.onsetSample(2000, rate);
        int peak = 0;
        for (int i = at; i < at + rate / 50; i++) {
            peak = Math.max(peak, Math.abs(pcm[i]));
        }
        assertTrue(peak > 3000, "audible onset " + peak);
        // Timbres differ: zero-crossing rate over the first 40 ms of each voice.
        int[] zc = new int[4];
        for (int v = 0; v < 4; v++) {
            double prev = 0;
            for (int i = 1; i < rate / 25; i++) {
                double x = EuclidTrack.voice(v, i / (double) rate);
                if (prev < 0 && x >= 0) {
                    zc[v]++;
                }
                prev = x;
            }
        }
        assertTrue(zc[EuclidSong.KICK] < zc[EuclidSong.CONGA] && zc[EuclidSong.CONGA] < zc[EuclidSong.BELL]
            && zc[EuclidSong.BELL] < zc[EuclidSong.CLAVE] * 2 && zc[EuclidSong.CLAVE] > 60, java.util.Arrays.toString(zc));
        String uri = EuclidTrack.dataUri(EuclidSong.PRESETS[1], 120);
        assertTrue(uri.startsWith("data:audio/wav;base64,UklGR"), "RIFF header");
    }
}
