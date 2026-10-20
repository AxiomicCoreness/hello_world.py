package com.fruitfly.games.rhythm.logic;

/** The stage's music-source picker: Euclidean rhythm (default), a local MIDI file, or a spoken line. */
public final class SongSource {
    public static final int EUCLID = 0;
    public static final int MIDI = 1;
    public static final int VOICE = 2;
    public static final int COUNT = 3;
    /** Shown when S / E / T or a picker button is used mid-song (fits the 390 px iPhone stage, like ControlMode.LOCK_HINT). */
    public static final String LOCK_HINT = "Picker locked during song - press R to restart";
    /** Longest centre-HUD hint that fits 390 CSS px at the iPhone HUD font (~7.8 px per monospace char). */
    public static final int MAX_HINT_CHARS = 48;
    private static final String[] LABELS = {"EUCLID", "MIDI", "VOICE"};
    private static final String[] IDS = {"euclid", "midi", "voice"};

    private SongSource() {
    }

    public static int next(int source, boolean running) {
        check(source);
        return running ? source : (source + 1) % COUNT;
    }

    public static String label(int source) {
        check(source);
        return LABELS[source];
    }

    /** ?source=euclid|midi|voice -> index, else -1. */
    public static int indexOf(String id) {
        for (int i = 0; i < IDS.length; i++) {
            if (IDS[i].equals(id)) {
                return i;
            }
        }
        return -1;
    }

    /** Label for the middle (item) button when the source is MIDI. Long names are cut to 14 chars. */
    public static String midiLabel(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return "PICK .MID";
        }
        String n = fileName;
        int dot = n.lastIndexOf('.');
        if (dot > 0) {
            n = n.substring(0, dot);
        }
        return n.length() > 14 ? n.substring(0, 13) + "\u2026" : n;
    }

    private static void check(int s) {
        if (s < 0 || s >= COUNT) {
            throw new IllegalArgumentException("source out of range: " + s);
        }
    }
}
