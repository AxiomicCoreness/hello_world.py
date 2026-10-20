package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

/** Standard MIDI File parsing: header, tracks, VLQ, running status, tempo map, note pairing, errors. */
class MidiTest {
    @Test
    void format0ScaleWithTempo() {
        Midi.Song s = Midi.parse(MidiBytes.scale());
        assertEquals(0, s.format);
        assertEquals(1, s.tracks);
        assertEquals(480, s.division);
        assertEquals(100.0, s.initialBpm(), 1e-9);
        assertEquals(16, s.notes.size());
        for (int i = 0; i < 16; i++) {
            assertEquals(i * 600.0, s.notes.get(i).startMs, 1e-9, "quarter = 600 ms at 100 BPM");
            assertEquals(600.0, s.notes.get(i).durationMs, 1e-9);
            assertEquals(100, s.notes.get(i).velocity);
        }
        assertEquals(60, s.notes.get(0).pitch);
        assertEquals(72, s.notes.get(7).pitch);
    }

    @Test
    void format1TempoMapFromTrack0AppliesToOtherTracks() {
        // Track 0: tempo 120 BPM at 0, 60 BPM from tick 960 (beat 2). Track 1: notes at ticks 0, 480, 960, 1440.
        MidiBytes.Track conductor = new MidiBytes.Track().tempo(0, 500_000).tempo(960, 1_000_000).end();
        MidiBytes.Track music = new MidiBytes.Track();
        for (int i = 0; i < 4; i++) {
            music.on(i == 0 ? 0 : 240, 1, 64 + i, 90).off(240, 1, 64 + i);
        }
        Midi.Song s = Midi.parse(MidiBytes.file(1, 480, conductor, music.end()));
        assertEquals(1, s.format);
        assertEquals(2, s.tracks);
        assertEquals(2, s.tempos.size());
        double[] want = {0, 500, 1000, 2000}; // 2 beats at 500 ms, then 1000 ms per beat
        for (int i = 0; i < 4; i++) {
            assertEquals(want[i], s.notes.get(i).startMs, 1e-9);
            assertEquals(1, s.notes.get(i).channel);
        }
        assertEquals(250.0, s.notes.get(0).durationMs, 1e-9);
        assertEquals(500.0, s.notes.get(3).durationMs, 1e-9, "half beat at 60 BPM");
        assertEquals(1500.0, Midi.tickToMs(1200, 480, s.tempos), 1e-9);
    }

    @Test
    void runningStatusVelocityZeroOffChordsAndMultiByteDeltas() {
        MidiBytes.Track t = new MidiBytes.Track()
            .delta(0).raw(0x90, 60, 80)          // C on
            .delta(0).raw(64, 80)                // E on (running status)
            .delta(0).raw(67, 80)                // G on
            .delta(200).raw(60, 0)               // C off via velocity 0 (running status)
            .delta(0).raw(0xB0, 7, 100)          // controller, 2 data bytes
            .delta(0).raw(0xC0, 5)               // program change, 1 data byte
            .delta(0).raw(0xF0, 2, 0x7E, 0xF7)   // sysex
            .delta(0).raw(0xFF, 0x03, 4, 'l', 'e', 'a', 'd') // track name meta
            .delta(16384).raw(0x80, 64, 0).delta(0).raw(0x80, 67, 0) // 3-byte VLQ delta
            .on(0, 0, 72, 127).off(96, 0, 72);
        Midi.Song s = Midi.parse(MidiBytes.file(0, 96, t.end()));
        assertEquals(4, s.notes.size());
        assertEquals(60, s.notes.get(0).pitch);
        assertEquals(64, s.notes.get(1).pitch);
        assertEquals(67, s.notes.get(2).pitch);
        assertEquals(0.0, s.notes.get(2).startMs, 1e-9);
        assertEquals(200 * 500.0 / 96, s.notes.get(0).durationMs, 1e-9);
        assertEquals((200 + 16384) * 500.0 / 96, s.notes.get(1).durationMs, 1e-9);
        assertEquals((200 + 16384) * 500.0 / 96, s.notes.get(3).startMs, 1e-9);
    }

    @Test
    void smpteDivisionAndUnknownChunksAndMissingNoteOff() {
        // 25 fps x 40 ticks per frame = 1000 ticks per second.
        MidiBytes.Track t = new MidiBytes.Track().on(0, 0, 50, 64).on(1000, 0, 55, 64);
        byte[] f = MidiBytes.file(0, 0xE728, t.end());
        byte[] withJunk = new byte[f.length + 12];
        System.arraycopy(f, 0, withJunk, 0, 14);
        byte[] junk = {'X', 'F', 'I', 'H', 0, 0, 0, 4, 1, 2, 3, 4};
        System.arraycopy(junk, 0, withJunk, 14, 12);
        System.arraycopy(f, 14, withJunk, 26, f.length - 14);
        Midi.Song s = Midi.parse(withJunk);
        assertEquals(2, s.notes.size());
        assertEquals(1000.0, s.notes.get(1).startMs, 1e-9);
        assertEquals(250.0, s.notes.get(0).durationMs, 1e-9, "unterminated notes get 250 ms");
    }

    @Test
    void rejectsMalformedInput() {
        assertThrows(IllegalArgumentException.class, () -> Midi.parse(new byte[] {1, 2, 3}));
        assertThrows(IllegalArgumentException.class, () -> Midi.parse("RIFF0000WAVEfmt ".getBytes()));
        byte[] f2 = MidiBytes.file(2, 96, new MidiBytes.Track().end());
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () -> Midi.parse(f2));
        assertTrue(e.getMessage().contains("format 2"));
        byte[] two = MidiBytes.file(0, 96, new MidiBytes.Track().end(), new MidiBytes.Track().end());
        assertThrows(IllegalArgumentException.class, () -> Midi.parse(two));
        byte[] ok = MidiBytes.scale();
        byte[] cut = java.util.Arrays.copyOf(ok, ok.length - 5);
        assertThrows(IllegalArgumentException.class, () -> Midi.parse(cut));
        byte[] noStatus = MidiBytes.file(0, 96, new MidiBytes.Track().delta(0).raw(60, 64).end());
        assertThrows(IllegalArgumentException.class, () -> Midi.parse(noStatus));
        byte[] longVlq = MidiBytes.file(0, 96, new MidiBytes.Track().raw(0x81, 0x81, 0x81, 0x81, 0x01, 0x90, 60, 64).end());
        assertThrows(IllegalArgumentException.class, () -> Midi.parse(longVlq));
    }

    @Test
    void vlqDecodesSpecExamples() {
        long[][] cases = {{0x00}, {0x40}, {0x7F}, {0x81, 0x00}, {0xC0, 0x00}, {0xFF, 0x7F}, {0x81, 0x80, 0x00}, {0xFF, 0xFF, 0x7F}, {0x81, 0x80, 0x80, 0x00}, {0xFF, 0xFF, 0xFF, 0x7F}};
        long[] want = {0, 0x40, 0x7F, 0x80, 0x2000, 0x3FFF, 0x4000, 0x1FFFFF, 0x200000, 0x0FFFFFFF};
        for (int i = 0; i < cases.length; i++) {
            byte[] b = new byte[cases[i].length];
            for (int j = 0; j < b.length; j++) {
                b[j] = (byte) cases[i][j];
            }
            long[] r = Midi.vlq(b, 0, b.length);
            assertEquals(want[i], r[0]);
            assertEquals(b.length, r[1]);
        }
        List<long[]> none = new java.util.ArrayList<>();
        assertEquals(500.0, Midi.tickToMs(96, 96, none), 1e-9, "default 120 BPM");
    }
}
