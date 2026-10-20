package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.List;

/**
 * "TTS voice" songs: a short line split into syllables, one syllable per
 * beat on a fixed grid, the line looped {@link #LOOPS} times. Syllable i of
 * loop l is a note at {@code LEAD_IN_MS + round((l * len + i) * 60000 / bpm)}
 * in lane (l * len + i) mod 4 (D F J K left to right). The page speaks each syllable with
 * the browser's speechSynthesis when its note comes up; the clock is a
 * synthesised click track, so the chart stays on time even when speech is
 * late or unavailable (then the syllables are only shown on the stage).
 */
public final class VoiceSong {
    public static final long LEAD_IN_MS = 2000;
    public static final int LOOPS = 4;
    /** How early (ms) the page asks the speech engine to start a syllable. */
    public static final long SPEAK_LEAD_MS = 60;

    /** Selectable lines: {id, button label, syllables separated by spaces}. */
    public static final String[][] LINES = {
        {"fly", "FRUIT FLY", "fruit fly brain keeps the beat"},
        {"count", "COUNT 1-4", "one and two and three and four and"},
        {"solfege", "DO RE MI", "do re mi fa sol la ti do"},
    };

    private VoiceSong() {
    }

    public static String[] syllables(int line) {
        return LINES[line][2].split(" ");
    }

    public static long noteMs(int index, int bpm) {
        if (bpm < 40 || bpm > 300) {
            throw new IllegalArgumentException("bpm out of range: " + bpm);
        }
        return LEAD_IN_MS + Math.round(index * 60_000.0 / bpm);
    }

    public static List<Note> notes(int line, int bpm) {
        String[] s = syllables(line);
        List<Note> out = new ArrayList<>();
        for (int l = 0; l < LOOPS; l++) {
            for (int i = 0; i < s.length; i++) {
                out.add(new Note((l * s.length + i) % RhythmGame.LANES, noteMs(l * s.length + i, bpm)));
            }
        }
        return out;
    }

    public static LoadedChart chart(int line, int bpm) {
        return new LoadedChart("Voice \u00b7 " + LINES[line][1], "speechSynthesis \u00b7 " + bpm + " BPM", bpm, 0, null,
                NoteChart.fromNotes(notes(line, bpm)));
    }

    /** The syllable sung by note {@code index} (in chart order). */
    public static String syllableAt(int line, int index) {
        String[] s = syllables(line);
        return s[index % s.length];
    }

    /** Index of the last note at or before song time {@code t}, or -1. */
    public static int currentIndex(int line, int bpm, long t) {
        int total = syllables(line).length * LOOPS;
        int idx = -1;
        for (int i = 0; i < total; i++) {
            if (noteMs(i, bpm) <= t) {
                idx = i;
            }
        }
        return idx;
    }

    /** Click-track length for the line: 1.5 s past the last syllable. */
    public static long durationMs(int line, int bpm) {
        return noteMs(syllables(line).length * LOOPS - 1, bpm) + 1500;
    }
}
