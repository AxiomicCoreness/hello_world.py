package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.jupiter.api.Test;

class ClickTrackTest {

    @Test
    void clicksStartOnEachBeatAndAreSilentBetween() {
        int rate = ClickTrack.SAMPLE_RATE;
        short[] s = ClickTrack.samples(120, 4000, rate);
        assertEquals(32000, s.length);
        int beat = rate / 2; // 120 bpm -> 4000 samples per beat
        int clickLen = (int) Math.ceil(ClickTrack.CLICK_S * rate);
        for (int k = 0; k < 8; k++) {
            int start = k * beat;
            assertEquals(0, s[start], "sin(0) = 0 at beat start " + k);
            int peak = 0;
            for (int i = start; i < start + clickLen; i++) {
                peak = Math.max(peak, Math.abs(s[i]));
            }
            assertTrue(peak > 10000, "click " + k + " peak " + peak);
            for (int i = start + clickLen; i < start + beat && i < s.length; i++) {
                assertEquals(0, s[i], "silence after click " + k + " at " + i);
            }
        }
    }

    @Test
    void timeSinceBeatNotSinceSongStart() {
        // Every non-accent click has identical samples, which only holds if tb restarts at each beat.
        short[] s = ClickTrack.samples(120, 4000, ClickTrack.SAMPLE_RATE);
        for (int i = 0; i < 240; i++) {
            assertEquals(s[4000 + i], s[8000 + i]);
            assertEquals(s[4000 + i], s[12000 + i]);
            assertEquals(s[i], s[16000 + i]); // beat 4 is the next accent
        }
    }

    @Test
    void nonIntegerBeatLengthRounds() {
        // 97 bpm at 8 kHz = 4948.45... samples per beat; beat 3 starts at round(14845.36) = 14845
        assertEquals(14845L, ClickTrack.beatStartSample(3, 97, 8000));
        short[] s = ClickTrack.samples(97, 2500, 8000);
        assertEquals(0, s[14844]);
        assertTrue(Math.abs(s[14846]) > 0);
    }

    @Test
    void wavHeaderAndBase64() {
        byte[] w = ClickTrack.wav(120, 1000, 8000);
        assertEquals(44 + 16000, w.length);
        assertEquals("RIFF", new String(w, 0, 4, StandardCharsets.US_ASCII));
        assertEquals("WAVEfmt ", new String(w, 8, 8, StandardCharsets.US_ASCII));
        assertEquals("data", new String(w, 36, 4, StandardCharsets.US_ASCII));
        assertEquals(16000, (w[40] & 0xff) | (w[41] & 0xff) << 8 | (w[42] & 0xff) << 16 | (w[43] & 0xff) << 24);
        assertEquals(8000, (w[24] & 0xff) | (w[25] & 0xff) << 8);
        String uri = ClickTrack.dataUri(120, 1000);
        assertTrue(uri.startsWith("data:audio/wav;base64,UklGR"));
        assertEquals(Base64.getEncoder().encodeToString(w), uri.substring("data:audio/wav;base64,".length()));
        for (int n = 0; n < 7; n++) {
            byte[] b = new byte[n];
            for (int i = 0; i < n; i++) {
                b[i] = (byte) (i * 97 - 3);
            }
            assertEquals(Base64.getEncoder().encodeToString(b), ClickTrack.base64(b));
        }
    }

    @Test
    void durationCoversLastNote() {
        LoadedChart c = new LoadedChart("t", "a", 120, -250, null,
                NoteChart.fromNotes(java.util.Arrays.asList(new Note(0, 3000))));
        assertEquals(3000 + 250 + 1500, ClickTrack.durationFor(c));
        assertThrows(IllegalArgumentException.class, () -> ClickTrack.samples(0, 1000, 8000));
        assertThrows(IllegalArgumentException.class, () -> ClickTrack.samples(120, 0, 8000));
    }
}
