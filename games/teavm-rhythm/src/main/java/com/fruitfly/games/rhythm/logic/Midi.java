package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.List;

/**
 * Standard MIDI File reader, pure Java (runs under TeaVM): formats 0 and 1,
 * PPQN or SMPTE division, variable-length quantities, running status,
 * meta / sysex skipping, the tempo map (meta 0x51 from any track) and
 * note-on / note-off pairing (note-on with velocity 0 is a note-off).
 *
 * Times: ticks are converted with the merged tempo map (default 500000
 * us per quarter = 120 BPM until the first tempo event), so a tempo change
 * at tick T affects only ticks after T. Malformed input throws
 * IllegalArgumentException with the byte offset.
 */
public final class Midi {
    public static final int MAX_NOTES = 20000;
    public static final int DEFAULT_TEMPO_US = 500_000;

    /** One sounding note: channel 0-15, pitch 0-127, velocity 1-127, start and length in ms. */
    public static final class NoteEvent {
        public final long tick;
        public final double startMs;
        public final double durationMs;
        public final int channel;
        public final int pitch;
        public final int velocity;

        NoteEvent(long tick, double startMs, double durationMs, int channel, int pitch, int velocity) {
            this.tick = tick;
            this.startMs = startMs;
            this.durationMs = durationMs;
            this.channel = channel;
            this.pitch = pitch;
            this.velocity = velocity;
        }
    }

    /** The parsed file. */
    public static final class Song {
        public final int format;
        public final int tracks;
        public final int division;
        /** Tempo map: {tick, microseconds per quarter}, sorted by tick. */
        public final List<long[]> tempos;
        /** Notes sorted by start time (stable: file order for equal times). */
        public final List<NoteEvent> notes;

        Song(int format, int tracks, int division, List<long[]> tempos, List<NoteEvent> notes) {
            this.format = format;
            this.tracks = tracks;
            this.division = division;
            this.tempos = tempos;
            this.notes = notes;
        }

        /** BPM of the first tempo in effect at tick 0. */
        public double initialBpm() {
            long us = DEFAULT_TEMPO_US;
            for (long[] t : tempos) {
                if (t[0] == 0) {
                    us = t[1];
                }
            }
            return 60_000_000.0 / us;
        }
    }

    private Midi() {
    }

    private static final class Raw {
        long tick;
        int channel;
        int pitch;
        int velocity;
        long offTick = -1;
        int order;
    }

    public static Song parse(byte[] b) {
        if (b == null || b.length < 14) {
            throw new IllegalArgumentException("not a MIDI file: too short");
        }
        if (!tag(b, 0, "MThd")) {
            throw new IllegalArgumentException("not a MIDI file: no MThd header");
        }
        long hlen = u32(b, 4);
        if (hlen < 6 || 8 + hlen > b.length) {
            throw new IllegalArgumentException("bad MThd length " + hlen);
        }
        int format = u16(b, 8);
        int ntrks = u16(b, 10);
        int division = u16(b, 12);
        if (format != 0 && format != 1) {
            throw new IllegalArgumentException("unsupported MIDI format " + format + " (0 and 1 are supported)");
        }
        if (format == 0 && ntrks != 1) {
            throw new IllegalArgumentException("format 0 needs exactly 1 track, got " + ntrks);
        }
        if (division == 0) {
            throw new IllegalArgumentException("division 0");
        }
        List<long[]> tempos = new ArrayList<>();
        List<Raw> raws = new ArrayList<>();
        int pos = (int) (8 + hlen);
        int found = 0;
        while (found < ntrks) {
            if (pos + 8 > b.length) {
                throw new IllegalArgumentException("missing track " + found + " of " + ntrks);
            }
            long len = u32(b, pos + 4);
            int start = pos + 8;
            if (start + len > b.length) {
                throw new IllegalArgumentException("track chunk at " + pos + " runs past the end");
            }
            if (tag(b, pos, "MTrk")) {
                readTrack(b, start, (int) (start + len), tempos, raws);
                found++;
            } // unknown chunk types are skipped, as the spec says
            pos = (int) (start + len);
        }
        sortTempos(tempos);
        List<NoteEvent> notes = new ArrayList<>(raws.size());
        for (Raw r : raws) {
            double s = tickToMs(r.tick, division, tempos);
            double e = r.offTick >= 0 ? tickToMs(r.offTick, division, tempos) : s + 250.0;
            notes.add(new NoteEvent(r.tick, s, Math.max(0.0, e - s), r.channel, r.pitch, r.velocity));
        }
        // Stable insertion sort by start time.
        for (int i = 1; i < notes.size(); i++) {
            NoteEvent x = notes.get(i);
            int j = i - 1;
            while (j >= 0 && notes.get(j).startMs > x.startMs) {
                notes.set(j + 1, notes.get(j));
                j--;
            }
            notes.set(j + 1, x);
        }
        return new Song(format, ntrks, division, tempos, notes);
    }

    private static void readTrack(byte[] b, int p, int end, List<long[]> tempos, List<Raw> raws) {
        long tick = 0;
        int status = 0;
        List<Raw> open = new ArrayList<>();
        while (p < end) {
            long[] v = vlq(b, p, end);
            tick += v[0];
            p = (int) v[1];
            if (p >= end) {
                throw new IllegalArgumentException("event missing after delta at " + p);
            }
            int c = b[p] & 0xff;
            if (c == 0xFF) {
                if (p + 2 > end) {
                    throw new IllegalArgumentException("truncated meta event at " + p);
                }
                int type = b[p + 1] & 0xff;
                long[] l = vlq(b, p + 2, end);
                int data = (int) l[1];
                if (data + l[0] > end) {
                    throw new IllegalArgumentException("meta event at " + p + " runs past the track");
                }
                if (type == 0x51) {
                    if (l[0] != 3) {
                        throw new IllegalArgumentException("tempo event at " + p + " has length " + l[0]);
                    }
                    long us = (b[data] & 0xffL) << 16 | (b[data + 1] & 0xffL) << 8 | (b[data + 2] & 0xffL);
                    if (us == 0) {
                        throw new IllegalArgumentException("tempo 0 at " + p);
                    }
                    tempos.add(new long[] {tick, us});
                }
                p = (int) (data + l[0]);
                if (type == 0x2F) {
                    break; // end of track
                }
                continue;
            }
            if (c == 0xF0 || c == 0xF7) {
                long[] l = vlq(b, p + 1, end);
                p = (int) (l[1] + l[0]);
                if (p > end) {
                    throw new IllegalArgumentException("sysex runs past the track");
                }
                status = 0; // sysex cancels running status
                continue;
            }
            int d1;
            if ((c & 0x80) != 0) {
                status = c;
                p++;
            } else if (status == 0) {
                throw new IllegalArgumentException("data byte without running status at " + p);
            }
            int kind = status & 0xF0;
            int ch = status & 0x0F;
            int n = kind == 0xC0 || kind == 0xD0 ? 1 : 2;
            if (p + n > end) {
                throw new IllegalArgumentException("truncated channel message at " + p);
            }
            d1 = b[p] & 0x7f;
            int d2 = n == 2 ? b[p + 1] & 0x7f : 0;
            p += n;
            if (kind == 0x90 && d2 > 0) {
                if (raws.size() >= MAX_NOTES) {
                    throw new IllegalArgumentException("more than " + MAX_NOTES + " notes");
                }
                Raw r = new Raw();
                r.tick = tick;
                r.channel = ch;
                r.pitch = d1;
                r.velocity = d2;
                r.order = raws.size();
                raws.add(r);
                open.add(r);
            } else if (kind == 0x80 || kind == 0x90) {
                for (int i = 0; i < open.size(); i++) { // first-on, first-off for repeated pitches
                    Raw r = open.get(i);
                    if (r.channel == ch && r.pitch == d1) {
                        r.offTick = tick;
                        open.remove(i);
                        break;
                    }
                }
            }
        }
    }

    private static void sortTempos(List<long[]> t) {
        for (int i = 1; i < t.size(); i++) {
            long[] x = t.get(i);
            int j = i - 1;
            while (j >= 0 && t.get(j)[0] > x[0]) {
                t.set(j + 1, t.get(j));
                j--;
            }
            t.set(j + 1, x);
        }
    }

    /** Milliseconds at {@code tick} under the tempo map (division: PPQN, or SMPTE when the top bit is set). */
    public static double tickToMs(long tick, int division, List<long[]> tempos) {
        if ((division & 0x8000) != 0) {
            int fps = -(byte) (division >> 8);
            int tpf = division & 0xff;
            double rate = (fps == 29 ? 29.97 : fps) * tpf;
            return tick * 1000.0 / rate;
        }
        double ms = 0;
        long lastTick = 0;
        long us = DEFAULT_TEMPO_US;
        for (long[] t : tempos) {
            if (t[0] >= tick) {
                break;
            }
            ms += (t[0] - lastTick) * us / 1000.0 / division;
            lastTick = t[0];
            us = t[1];
        }
        return ms + (tick - lastTick) * us / 1000.0 / division;
    }

    /** {value, next offset}. At most 4 bytes, as the spec says. */
    static long[] vlq(byte[] b, int p, int end) {
        long v = 0;
        for (int i = 0; i < 4; i++) {
            if (p >= end) {
                throw new IllegalArgumentException("truncated variable-length number at " + p);
            }
            int c = b[p++] & 0xff;
            v = (v << 7) | (c & 0x7f);
            if ((c & 0x80) == 0) {
                return new long[] {v, p};
            }
        }
        throw new IllegalArgumentException("variable-length number longer than 4 bytes at " + (p - 4));
    }

    private static boolean tag(byte[] b, int at, String s) {
        if (at + 4 > b.length) {
            return false;
        }
        for (int i = 0; i < 4; i++) {
            if (b[at + i] != (byte) s.charAt(i)) {
                return false;
            }
        }
        return true;
    }

    private static int u16(byte[] b, int at) {
        return (b[at] & 0xff) << 8 | (b[at + 1] & 0xff);
    }

    private static long u32(byte[] b, int at) {
        return (b[at] & 0xffL) << 24 | (b[at + 1] & 0xffL) << 16 | (b[at + 2] & 0xffL) << 8 | (b[at + 3] & 0xffL);
    }
}
