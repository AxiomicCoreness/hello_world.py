package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

/** Music-source picker, MIDI -> lanes / chart / audio, the voice line grid, and the fly playing every source. */
class MusicSourceTest {
    @Test
    void pickerCyclesEuclidMidiVoiceAndLocksDuringASong() {
        assertEquals(SongSource.MIDI, SongSource.next(SongSource.EUCLID, false));
        assertEquals(SongSource.VOICE, SongSource.next(SongSource.MIDI, false));
        assertEquals(SongSource.EUCLID, SongSource.next(SongSource.VOICE, false));
        for (int s = 0; s < SongSource.COUNT; s++) {
            assertEquals(s, SongSource.next(s, true));
        }
        assertEquals("EUCLID", SongSource.label(SongSource.EUCLID));
        assertEquals(SongSource.VOICE, SongSource.indexOf("voice"));
        assertEquals(-1, SongSource.indexOf("x"));
        assertEquals("PICK .MID", SongSource.midiLabel(null));
        assertEquals("scale", SongSource.midiLabel("scale.mid"));
        assertEquals("a_very_long_n\u2026", SongSource.midiLabel("a_very_long_name_indeed.midi"));
        assertThrows(IllegalArgumentException.class, () -> SongSource.label(3));
        assertEquals(InputRouter.CYCLE_SOURCE, InputRouter.key("s", "KeyS", false, false));
        assertEquals(InputRouter.LOCKED, InputRouter.key("s", "KeyS", false, true));
        // Both lock hints fit one centre-HUD line on the 390 px stage (a 51-char hint overflowed in Chrome).
        assertTrue(SongSource.LOCK_HINT.length() <= SongSource.MAX_HINT_CHARS, SongSource.LOCK_HINT);
        assertTrue(ControlMode.LOCK_HINT.length() <= SongSource.MAX_HINT_CHARS, ControlMode.LOCK_HINT);
        assertTrue(SongSource.LOCK_HINT.contains("press R"));
    }

    @Test
    void midiLanesByPitchQuartile() {
        Midi.Song s = Midi.parse(MidiBytes.scale());
        int[] cuts = MidiSong.quartileCuts(s.notes);
        assertArrayEquals(new int[] {64, 67, 71}, cuts); // sorted: 60 60 62 62 | 64 64 65 65 | 67 67 69 69 | 71 71 72 72
        assertEquals(0, MidiSong.laneFor(60, cuts));
        assertEquals(0, MidiSong.laneFor(62, cuts));
        assertEquals(1, MidiSong.laneFor(65, cuts));
        assertEquals(2, MidiSong.laneFor(69, cuts));
        assertEquals(3, MidiSong.laneFor(72, cuts));
        List<Note> n = MidiSong.notes(s);
        assertEquals(16, n.size());
        int[] lanes = new int[4];
        for (int i = 0; i < n.size(); i++) {
            assertEquals(2000 + 600L * i, n.get(i).timeMs(), "first note at 2000 ms, then the MIDI timing");
            lanes[n.get(i).lane()]++;
        }
        assertArrayEquals(new int[] {4, 4, 4, 4}, lanes);
        LoadedChart c = MidiSong.chart(s, "scale");
        assertEquals("MIDI \u00b7 scale", c.title());
        assertEquals("format 0 \u00b7 1 track \u00b7 100 BPM", c.artist());
    }

    @Test
    void midiChordsSpreadAcrossLanesAndDenseRunsAreThinned() {
        MidiBytes.Track t = new MidiBytes.Track();
        for (int i = 0; i < 8; i++) { // C-E-G-C chords every quarter at 120 BPM
            t.on(i == 0 ? 0 : 96, 0, 48, 90).on(0, 0, 64, 90).on(0, 0, 67, 90).on(0, 0, 84, 90)
                .off(96, 0, 48).off(0, 0, 64).off(0, 0, 67).off(0, 0, 84);
        }
        for (int i = 0; i < 8; i++) { // then 32nd-note trill on one pitch: 62.5 ms apart
            t.on(0, 0, 84, 90).off(24, 0, 84);
        }
        Midi.Song s = Midi.parse(MidiBytes.file(0, 192, t.end()));
        List<Note> n = MidiSong.notes(s);
        for (int i = 0; i < 8; i++) {
            for (int j = 0; j < 4; j++) {
                assertEquals(j, n.get(i * 4 + j).lane(), "chord tone " + j + " in lane " + j);
            }
        }
        long prevK = -1;
        for (Note x : n) {
            if (x.lane() == 3) {
                assertTrue(prevK < 0 || x.timeMs() - prevK >= MidiSong.MIN_LANE_GAP_MS);
                prevK = x.timeMs();
            }
        }
        assertTrue(n.size() < 32 + 8, "trill thinned: " + n.size());
        assertThrows(IllegalArgumentException.class, () -> MidiSong.chart(Midi.parse(MidiBytes.file(0, 96, new MidiBytes.Track().end())), "x"));
    }

    @Test
    void midiAudioSoundsEveryNoteAtItsPitch() {
        Midi.Song s = Midi.parse(MidiBytes.scale());
        int rate = MidiSong.SAMPLE_RATE;
        short[] pcm = MidiSong.samples(s, rate);
        for (int i = 0; i < EuclidTrack.onsetSample(1995, rate); i++) {
            assertEquals(0, pcm[i]);
        }
        // Zero crossings over 100 ms of the first note (C4, 261.6 Hz, + 3rd harmonic) ~ 26 per 100 ms.
        int a = EuclidTrack.onsetSample(2000, rate);
        int zc = 0;
        for (int i = a + 1; i < a + rate / 10; i++) {
            if (pcm[i - 1] < 0 && pcm[i] >= 0) {
                zc++;
            }
        }
        assertTrue(zc >= 20 && zc <= 40, "C4 crossings " + zc);
        assertEquals(261.63, MidiSong.pitchHz(60), 0.01);
        assertTrue(MidiSong.dataUri(s).startsWith("data:audio/wav;base64,UklGR"));
    }

    @Test
    void voiceLinesSitOnAFixedBeatGrid() {
        assertArrayEquals(new String[] {"fruit", "fly", "brain", "keeps", "the", "beat"}, VoiceSong.syllables(0));
        List<Note> n = VoiceSong.notes(0, 120);
        assertEquals(6 * VoiceSong.LOOPS, n.size());
        for (int i = 0; i < n.size(); i++) {
            assertEquals(2000 + 500L * i, n.get(i).timeMs());
            assertEquals(i % 4, n.get(i).lane());
        }
        assertEquals("brain", VoiceSong.syllableAt(0, 8));
        assertEquals(-1, VoiceSong.currentIndex(0, 120, 1999));
        assertEquals(0, VoiceSong.currentIndex(0, 120, 2000));
        assertEquals(3, VoiceSong.currentIndex(0, 120, 3700));
        assertEquals(2000 + 500L * 23 + 1500, VoiceSong.durationMs(0, 120));
        assertEquals("Voice \u00b7 FRUIT FLY", VoiceSong.chart(0, 120).title());
    }

    @Test
    void everyFlyModePlaysMidiAndVoiceCharts() {
        MidiBytes.Track t = new MidiBytes.Track().tempo(0, 400_000);
        int[] riff = {40, 52, 55, 59, 64, 59, 55, 52, 43, 55, 59, 62, 67, 62, 59, 55};
        for (int bar = 0; bar < 4; bar++) {
            for (int x : riff) {
                t.on(0, 0, x, 100).on(0, 1, x + 12, 70).off(240, 0, x).off(0, 1, x + 12); // 8ths + octave doubling
            }
        }
        NoteChart[] charts = {
            MidiSong.chart(Midi.parse(MidiBytes.scale()), "scale").chart(),
            MidiSong.chart(Midi.parse(MidiBytes.file(0, 480, t.end())), "riff").chart(),
            VoiceSong.chart(0, 140).chart(), VoiceSong.chart(1, 90).chart(), VoiceSong.chart(2, 120).chart(),
        };
        for (NoteChart c : charts) {
            for (int mode : FlyPlay.MODES) {
                long[] r = FlyPlay.play(c, mode, 16);
                String what = "mode " + mode + " P/Gr/Go/M " + r[1] + "/" + r[2] + "/" + r[3] + "/" + r[4] + " of " + r[5];
                assertEquals(0, r[4], what);
                assertEquals(r[5], r[1] + r[2] + r[3], what);
            }
        }
    }
}
