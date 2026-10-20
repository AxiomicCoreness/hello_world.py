package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.List;

/**
 * "Euclidean rhythm" custom songs: presets of one or more E(k, n) layers,
 * each on its own lane (D kick, F tresillo, J cinquillo, K bell) with its own
 * synthesised timbre ({@link EuclidTrack}). Every pattern spans one 4/4 bar
 * whatever its step count, so E(3,8) / E(5,8) steps are eighth notes, E(4,16)
 * sixteenths and E(7,12) triplet eighths. Each pulse is one note.
 *
 * Step i of bar b is at {@code LEAD_IN_MS + round((b * n + i) * barMs / n)},
 * barMs = 240000 / bpm. Song time 0 is audio sample 0 (offset 0).
 */
public final class EuclidSong {
    public static final long LEAD_IN_MS = 2000;
    public static final int BARS = 8;
    public static final int[] BPMS = {90, 100, 120, 140};
    public static final int DEFAULT_BPM_INDEX = 2;

    /** Timbres, one per lane. */
    public static final int KICK = 0;
    public static final int CLAVE = 1;
    public static final int CONGA = 2;
    public static final int BELL = 3;

    /** One E(k, n) layer, rotated left by {@code rotation}, on {@code lane} with {@code timbre}. */
    public static final class Layer {
        public final String name;
        public final int k;
        public final int n;
        public final int rotation;
        public final int lane;
        public final int timbre;

        Layer(String name, int k, int n, int rotation, int lane, int timbre) {
            this.name = name;
            this.k = k;
            this.n = n;
            this.rotation = rotation;
            this.lane = lane;
            this.timbre = timbre;
        }

        public boolean[] steps() {
            return Euclid.rotate(Euclid.pattern(k, n), rotation);
        }

        public String text() {
            return Euclid.toText(steps());
        }

        /** "E(3,8)" */
        public String formula() {
            return "E(" + k + "," + n + ")";
        }
    }

    static final Layer KICK_4_16 = new Layer("kick", 4, 16, 0, 0, KICK);
    static final Layer TRESILLO = new Layer("tresillo", 3, 8, 0, 1, CLAVE);
    static final Layer CINQUILLO = new Layer("cinquillo", 5, 8, 0, 2, CONGA);
    static final Layer BEMBE = new Layer("bembe bell", 7, 12, 0, 3, BELL);

    /** A selectable preset: a label and its layers. */
    public static final class Preset {
        public final String id;
        public final String label;
        private final Layer[] layers;

        Preset(String id, String label, Layer... layers) {
            this.id = id;
            this.label = label;
            this.layers = layers;
        }

        public Layer[] layers() {
            return layers.clone();
        }
    }

    public static final Preset[] PRESETS = {
        new Preset("layered", "LAYERED x4", KICK_4_16, TRESILLO, CINQUILLO, BEMBE),
        new Preset("tresillo", "TRESILLO E(3,8)", TRESILLO),
        new Preset("cinquillo", "CINQUILLO E(5,8)", CINQUILLO),
        new Preset("bembe", "BEMBE E(7,12)", BEMBE),
        new Preset("kick", "KICK E(4,16)", KICK_4_16),
    };

    private EuclidSong() {
    }

    /** Index of a preset id (e.g. from ?rhythm=), or -1. */
    public static int indexOf(String id) {
        for (int i = 0; i < PRESETS.length; i++) {
            if (PRESETS[i].id.equals(id)) {
                return i;
            }
        }
        return -1;
    }

    public static long barMs(int bpm) {
        checkBpm(bpm);
        return 240_000L / bpm;
    }

    private static void checkBpm(int bpm) {
        if (bpm < 40 || bpm > 300) {
            throw new IllegalArgumentException("bpm out of range: " + bpm);
        }
    }

    /** Note time of step {@code step} of bar {@code bar} for an n-step layer. */
    public static long stepMs(int bar, int step, int n, int bpm) {
        checkBpm(bpm);
        return LEAD_IN_MS + Math.round((bar * (double) n + step) * 240_000.0 / bpm / n);
    }

    /** Notes for a preset: every pulse of every layer, {@code bars} bars. */
    public static List<Note> notes(Preset p, int bpm, int bars) {
        if (bars < 1 || bars > 64) {
            throw new IllegalArgumentException("bars out of range: " + bars);
        }
        List<Note> out = new ArrayList<>();
        for (int b = 0; b < bars; b++) {
            for (Layer l : p.layers) {
                boolean[] s = l.steps();
                for (int i = 0; i < s.length; i++) {
                    if (s[i]) {
                        out.add(new Note(l.lane, stepMs(b, i, l.n, bpm)));
                    }
                }
            }
        }
        return out;
    }

    /** The chart as a LoadedChart (offset 0, audio synthesised by the page). */
    public static LoadedChart chart(Preset p, int bpm) {
        NoteChart c = NoteChart.fromNotes(notes(p, bpm, BARS));
        return new LoadedChart("Euclid \u00b7 " + p.label, "Bjorklund \u00b7 " + bpm + " BPM", bpm, 0, null, c);
    }

    /** HUD lines: "D kick      E(4,16)  x...x...x...x...". */
    public static List<String> hudLines(Preset p) {
        List<String> out = new ArrayList<>();
        for (Layer l : p.layers) {
            out.add(RhythmGame.LANE_KEYS[l.lane] + " " + l.formula() + " " + l.text());
        }
        return out;
    }

    /** Label for the BPM button. */
    public static String bpmLabel(int bpm) {
        return bpm + " BPM";
    }
}
