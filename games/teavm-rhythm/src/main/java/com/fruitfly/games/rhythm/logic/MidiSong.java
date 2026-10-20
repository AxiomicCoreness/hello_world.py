package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * A parsed MIDI file as a playable chart plus its synthesised audio.
 *
 * Lanes by pitch quartile: the sorted pitches of all notes are cut at the
 * 25 / 50 / 75 % ranks; lane = how many cut points the pitch reaches, so low
 * notes go to D and high notes to K. To stay playable, a note within
 * {@link #MIN_LANE_GAP_MS} of the previous kept note in its lane is not a
 * chart note (it still sounds). Song time = MIDI time - first note + 2000 ms,
 * at most {@link #MAX_SONG_MS}.
 *
 * Audio: every MIDI note (kept or not) is rendered as an oscillator voice
 * (sine + 1/3 third harmonic, 5 ms attack, exponential release) at its pitch,
 * into 11025 Hz PCM. The page plays it through the same audio element as the
 * click track, so the audio position drives SongClock (no live WebAudio graph
 * whose clock could drift from the chart).
 */
public final class MidiSong {
    public static final long LEAD_IN_MS = 2000;
    public static final long MIN_LANE_GAP_MS = 180;
    public static final long MAX_SONG_MS = 180_000;
    public static final int SAMPLE_RATE = 11025;
    static final double VOICE_MAX_S = 0.6;

    private MidiSong() {
    }

    /** The three cut points (pitches) for the quartile lanes. */
    public static int[] quartileCuts(List<Midi.NoteEvent> notes) {
        int n = notes.size();
        int[] p = new int[n];
        for (int i = 0; i < n; i++) {
            p[i] = notes.get(i).pitch;
        }
        Arrays.sort(p);
        int[] cuts = new int[3];
        for (int j = 0; j < 3; j++) {
            cuts[j] = n == 0 ? 128 : p[Math.min(n - 1, (j + 1) * n / 4)];
        }
        return cuts;
    }

    public static int laneFor(int pitch, int[] cuts) {
        int lane = 0;
        for (int c : cuts) {
            if (pitch >= c) {
                lane++;
            }
        }
        return Math.min(lane, RhythmGame.LANES - 1);
    }

    /** Song-time ms of a MIDI note. */
    static long songMs(Midi.Song s, Midi.NoteEvent e) {
        double first = s.notes.isEmpty() ? 0 : s.notes.get(0).startMs;
        return LEAD_IN_MS + Math.round(e.startMs - first);
    }

    public static List<Note> notes(Midi.Song s) {
        int[] cuts = quartileCuts(s.notes);
        long[] last = new long[RhythmGame.LANES];
        Arrays.fill(last, Long.MIN_VALUE / 2);
        List<Note> out = new ArrayList<>();
        for (Midi.NoteEvent e : s.notes) {
            long t = songMs(s, e);
            if (t > MAX_SONG_MS) {
                break;
            }
            int lane = laneFor(e.pitch, cuts);
            if (t - last[lane] < MIN_LANE_GAP_MS) {
                continue;
            }
            last[lane] = t;
            out.add(new Note(lane, t));
        }
        return out;
    }

    public static LoadedChart chart(Midi.Song s, String name) {
        List<Note> n = notes(s);
        if (n.isEmpty()) {
            throw new IllegalArgumentException("MIDI file has no notes");
        }
        String title = name == null || name.isEmpty() ? "MIDI" : name;
        return new LoadedChart("MIDI \u00b7 " + title, "format " + s.format + " \u00b7 " + s.tracks + " track"
                + (s.tracks == 1 ? "" : "s") + " \u00b7 " + Math.round(s.initialBpm()) + " BPM", s.initialBpm(), 0, null,
                NoteChart.fromNotes(n));
    }

    public static double pitchHz(int pitch) {
        return 440.0 * Math.pow(2.0, (pitch - 69) / 12.0);
    }

    public static short[] samples(Midi.Song s, int rate) {
        long end = 0;
        for (Midi.NoteEvent e : s.notes) {
            long t = songMs(s, e);
            if (t > MAX_SONG_MS) {
                break;
            }
            end = Math.max(end, t + Math.round(Math.min(VOICE_MAX_S * 1000, e.durationMs + 150)));
        }
        double[] mix = new double[(int) ((end + 1000) * rate / 1000L)];
        for (Midi.NoteEvent e : s.notes) {
            long t = songMs(s, e);
            if (t > MAX_SONG_MS) {
                break;
            }
            int start = EuclidTrack.onsetSample(t, rate);
            double hold = Math.min(VOICE_MAX_S, e.durationMs / 1000.0);
            int len = (int) Math.ceil(Math.min(VOICE_MAX_S, hold + 0.15) * rate);
            double w = 2 * Math.PI * pitchHz(e.pitch) / rate;
            double amp = 0.25 * e.velocity / 127.0;
            for (int i = 0; i < len && start + i < mix.length; i++) {
                double ts = i / (double) rate;
                double env = Math.min(1.0, ts / 0.005) * (ts < hold ? Math.exp(-ts / 0.4) : Math.exp(-hold / 0.4) * Math.exp(-(ts - hold) / 0.04));
                mix[start + i] += amp * env * (Math.sin(w * i) + Math.sin(3 * w * i) / 3.0);
            }
        }
        return EuclidTrack.toPcm(mix);
    }

    public static String dataUri(Midi.Song s) {
        return ClickTrack.wavDataUri(samples(s, SAMPLE_RATE), SAMPLE_RATE);
    }
}
