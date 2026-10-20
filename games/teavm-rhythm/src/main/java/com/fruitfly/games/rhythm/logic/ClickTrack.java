package com.fruitfly.games.rhythm.logic;

/**
 * Synthesises a metronome click track as a mono 16-bit PCM WAV, so the page
 * can test audio sync without shipping a binary file.
 *
 * Each beat k starts at sample round(k * rate * 60 / bpm). Inside a beat, with
 * tb = seconds since that beat's start (not since the song start), a click is
 * {@code AMPLITUDE * exp(-tb / DECAY_S) * sin(2 pi f tb)} for tb &lt; CLICK_S,
 * then silence. f is 1500 Hz on the first beat of each 4-beat bar and 1000 Hz
 * otherwise. tools/gen_click_track.py writes the same samples.
 */
public final class ClickTrack {
    public static final int SAMPLE_RATE = 8000;
    static final double CLICK_S = 0.030;
    static final double DECAY_S = 0.008;
    static final double AMPLITUDE = 0.6 * 32767.0;
    static final double ACCENT_HZ = 1500.0;
    static final double BEAT_HZ = 1000.0;

    private ClickTrack() {
    }

    /** First sample of beat k. */
    static long beatStartSample(long k, double bpm, int rate) {
        return Math.round(k * rate * 60.0 / bpm);
    }

    /** PCM samples for {@code durationMs} of clicks at {@code bpm}, beat 0 at sample 0. */
    public static short[] samples(double bpm, long durationMs, int rate) {
        if (!(bpm > 0.0 && bpm <= ChartJson.MAX_BPM)) {
            throw new IllegalArgumentException("bpm out of range: " + bpm);
        }
        if (durationMs <= 0 || durationMs > 600_000L) {
            throw new IllegalArgumentException("durationMs out of range: " + durationMs);
        }
        if (rate < 1000 || rate > 192_000) {
            throw new IllegalArgumentException("rate out of range: " + rate);
        }
        int n = (int) (durationMs * rate / 1000L);
        short[] out = new short[n];
        long k = 0;
        long start = 0;
        long next = beatStartSample(1, bpm, rate);
        for (int i = 0; i < n; i++) {
            while (i >= next) {
                k++;
                start = next;
                next = beatStartSample(k + 1, bpm, rate);
            }
            double tb = (i - start) / (double) rate;
            if (tb < CLICK_S) {
                double f = k % 4 == 0 ? ACCENT_HZ : BEAT_HZ;
                double v = AMPLITUDE * Math.exp(-tb / DECAY_S) * Math.sin(2.0 * Math.PI * f * tb);
                out[i] = (short) Math.round(v);
            }
        }
        return out;
    }

    /** The samples wrapped in a 44-byte RIFF/WAVE header (PCM, mono, 16-bit, little-endian). */
    public static byte[] wav(double bpm, long durationMs, int rate) {
        short[] pcm = samples(bpm, durationMs, rate);
        int dataLen = pcm.length * 2;
        byte[] b = new byte[44 + dataLen];
        ascii(b, 0, "RIFF");
        le32(b, 4, 36 + dataLen);
        ascii(b, 8, "WAVE");
        ascii(b, 12, "fmt ");
        le32(b, 16, 16);
        le16(b, 20, 1);          // PCM
        le16(b, 22, 1);          // mono
        le32(b, 24, rate);
        le32(b, 28, rate * 2);   // byte rate
        le16(b, 32, 2);          // block align
        le16(b, 34, 16);         // bits per sample
        ascii(b, 36, "data");
        le32(b, 40, dataLen);
        for (int i = 0; i < pcm.length; i++) {
            le16(b, 44 + 2 * i, pcm[i]);
        }
        return b;
    }

    /** {@code data:audio/wav;base64,...} for an audio element's src. */
    public static String dataUri(double bpm, long durationMs) {
        return "data:audio/wav;base64," + base64(wav(bpm, durationMs, SAMPLE_RATE));
    }

    /**
     * Track length for a loaded chart: up to 1.5 s past the audio position of
     * its last note (lastNote - offset), at least 1 s.
     */
    public static long durationFor(LoadedChart c) {
        long lastAudioMs = c.chart().lastNoteMs() - c.offsetMs();
        return Math.max(1000L, lastAudioMs + 1500L);
    }

    private static void ascii(byte[] b, int at, String s) {
        for (int i = 0; i < s.length(); i++) {
            b[at + i] = (byte) s.charAt(i);
        }
    }

    private static void le16(byte[] b, int at, int v) {
        b[at] = (byte) v;
        b[at + 1] = (byte) (v >> 8);
    }

    private static void le32(byte[] b, int at, int v) {
        le16(b, at, v);
        le16(b, at + 2, v >> 16);
    }

    private static final char[] B64 =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".toCharArray();

    /** Standard base64 with padding (RFC 4648). */
    static String base64(byte[] in) {
        StringBuilder sb = new StringBuilder((in.length + 2) / 3 * 4);
        int i = 0;
        for (; i + 2 < in.length; i += 3) {
            int v = (in[i] & 0xff) << 16 | (in[i + 1] & 0xff) << 8 | (in[i + 2] & 0xff);
            sb.append(B64[v >>> 18]).append(B64[(v >>> 12) & 63]).append(B64[(v >>> 6) & 63]).append(B64[v & 63]);
        }
        int rem = in.length - i;
        if (rem == 1) {
            int v = (in[i] & 0xff) << 16;
            sb.append(B64[v >>> 18]).append(B64[(v >>> 12) & 63]).append("==");
        } else if (rem == 2) {
            int v = (in[i] & 0xff) << 16 | (in[i + 1] & 0xff) << 8;
            sb.append(B64[v >>> 18]).append(B64[(v >>> 12) & 63]).append(B64[(v >>> 6) & 63]).append('=');
        }
        return sb.toString();
    }
}
