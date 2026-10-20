package com.fruitfly.games.rhythm.logic;

/**
 * A chart read from JSON: its metadata plus the notes as a {@link NoteChart}.
 *
 * offsetMs maps the audio clock onto chart time:
 * {@code songTimeMs = audioPositionMs + offsetMs}. A positive offset makes
 * every note due that many ms earlier against the audio; a negative one, later.
 */
public final class LoadedChart {
    private final String title;
    private final String artist;
    private final double bpm;
    private final long offsetMs;
    private final String audio;
    private final NoteChart chart;

    public LoadedChart(String title, String artist, double bpm, long offsetMs, String audio, NoteChart chart) {
        if (title == null || artist == null || chart == null) {
            throw new IllegalArgumentException("title, artist and chart are required");
        }
        this.title = title;
        this.artist = artist;
        this.bpm = bpm;
        this.offsetMs = offsetMs;
        this.audio = audio;
        this.chart = chart;
    }

    public String title() {
        return title;
    }

    public String artist() {
        return artist;
    }

    public double bpm() {
        return bpm;
    }

    public long offsetMs() {
        return offsetMs;
    }

    /** Optional metadata.audio (a URL relative to the page), or null. */
    public String audio() {
        return audio;
    }

    /** The notes, sorted by time. Call {@link NoteChart#fresh()} for each new run. */
    public NoteChart chart() {
        return chart;
    }
}
