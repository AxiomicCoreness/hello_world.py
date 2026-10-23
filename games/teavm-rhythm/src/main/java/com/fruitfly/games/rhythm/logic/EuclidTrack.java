package com.fruitfly.games.rhythm.logic;

import java.util.List;

/**
 * Synthesises the audio for a Euclidean song as 16-bit mono PCM (then a WAV
 * data URI via {@link ClickTrack#wavDataUri}), so no binary audio is
 * committed and the page's existing audio clock (AudioSync -> SongClock)
 * stays the time source. Each layer has its own timbre, every pulse sounds
 * exactly at its note time (sample round(t * rate / 1000)):
 * <ul>
 * <li>KICK: sine sweeping 150 -&gt; 50 Hz, 120 ms decay</li>
 * <li>CLAVE: 2500 Hz sine, 20 ms decay</li>
 * <li>CONGA: 330 Hz + 0.35 x 660 Hz sines, 70 ms decay</li>
 * <li>BELL: inharmonic partials 1320 x {1, 2.76, 5.40} Hz, 150 ms decay</li>
 * </ul>
 */
public final class EuclidTrack {
    public static final int SAMPLE_RATE = 16000;
    static final double GAIN = 0.32 * 32767.0;

    private EuclidTrack() {
    }

    /** Length in seconds of each timbre's hit. */
    static double lengthS(int timbre) {
        switch (timbre) {
            case EuclidSong.KICK: return 0.30;
            case EuclidSong.CLAVE: return 0.08;
            case EuclidSong.CONGA: return 0.25;
            default: return 0.45;
        }
    }

    /** One hit of {@code timbre} at t seconds after its onset, in [-1, 1]. */
    static double voice(int timbre, double t) {
        switch (timbre) {
            case EuclidSong.KICK: {
                double phase = 2 * Math.PI * (50 * t + 100 * 0.03 * (1 - Math.exp(-t / 0.03)));
                return Math.exp(-t / 0.12) * Math.sin(phase);
            }
            case EuclidSong.CLAVE:
                return Math.exp(-t / 0.02) * Math.sin(2 * Math.PI * 2500 * t);
            case EuclidSong.CONGA:
                return Math.exp(-t / 0.07) * (Math.sin(2 * Math.PI * 330 * t) + 0.35 * Math.sin(2 * Math.PI * 660 * t)) / 1.35;
            default: {
                double f = 1320;
                return Math.exp(-t / 0.15) * (Math.sin(2 * Math.PI * f * t) + 0.5 * Math.sin(2 * Math.PI * f * 2.76 * t)
                        + 0.25 * Math.sin(2 * Math.PI * f * 5.40 * t)) / 1.75;
            }
        }
    }

    /** PCM for a preset: all pulses of all bars, plus 1.5 s tail. */
    public static short[] samples(EuclidSong.Preset p, int bpm, int rate) {
        List<Note> notes = EuclidSong.notes(p, bpm, EuclidSong.BARS);
        long last = 0;
        for (Note n : notes) {
            last = Math.max(last, n.timeMs());
        }
        int len = (int) ((last + 1500) * rate / 1000L);
        double[] mix = new double[len];
        int[] timbre = EuclidSong.timbres(p, EuclidSong.BARS); // same order as notes(), lane-independent
        for (int k = 0; k < notes.size(); k++) {
            addHit(mix, onsetSample(notes.get(k).timeMs(), rate), timbre[k], rate);
        }
        return toPcm(mix);
    }

    /** First sample of a hit at {@code timeMs}. */
    public static int onsetSample(long timeMs, int rate) {
        return (int) Math.round(timeMs * (double) rate / 1000.0);
    }

    static void addHit(double[] mix, int start, int timbre, int rate) {
        int len = (int) Math.ceil(lengthS(timbre) * rate);
        for (int i = 0; i < len && start + i < mix.length; i++) {
            mix[start + i] += voice(timbre, i / (double) rate);
        }
    }

    static short[] toPcm(double[] mix) {
        short[] out = new short[mix.length];
        for (int i = 0; i < mix.length; i++) {
            double v = Math.max(-1.0, Math.min(1.0, mix[i])) * GAIN;
            out[i] = (short) Math.round(v);
        }
        return out;
    }

    public static String dataUri(EuclidSong.Preset p, int bpm) {
        return ClickTrack.wavDataUri(samples(p, bpm, SAMPLE_RATE), SAMPLE_RATE);
    }
}
