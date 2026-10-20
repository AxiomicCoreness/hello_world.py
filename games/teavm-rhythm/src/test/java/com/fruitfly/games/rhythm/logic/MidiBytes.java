package com.fruitfly.games.rhythm.logic;

import java.io.ByteArrayOutputStream;

/** Builds Standard MIDI File bytes in tests, so no binary .mid is committed. */
final class MidiBytes {
    private MidiBytes() {
    }

    static final class Track {
        final ByteArrayOutputStream b = new ByteArrayOutputStream();

        Track delta(long d) {
            vlq(b, d);
            return this;
        }

        Track raw(int... bytes) {
            for (int x : bytes) {
                b.write(x);
            }
            return this;
        }

        Track on(long d, int ch, int pitch, int vel) {
            return delta(d).raw(0x90 | ch, pitch, vel);
        }

        Track off(long d, int ch, int pitch) {
            return delta(d).raw(0x80 | ch, pitch, 0);
        }

        Track tempo(long d, long usPerQuarter) {
            return delta(d).raw(0xFF, 0x51, 3, (int) (usPerQuarter >> 16) & 0xff, (int) (usPerQuarter >> 8) & 0xff, (int) usPerQuarter & 0xff);
        }

        Track end() {
            return delta(0).raw(0xFF, 0x2F, 0);
        }

        byte[] bytes() {
            return b.toByteArray();
        }
    }

    static void vlq(ByteArrayOutputStream o, long v) {
        int[] tmp = new int[5];
        int n = 0;
        tmp[n++] = (int) (v & 0x7f);
        v >>= 7;
        while (v > 0) {
            tmp[n++] = (int) (v & 0x7f) | 0x80;
            v >>= 7;
        }
        for (int i = n - 1; i >= 0; i--) {
            o.write(tmp[i]);
        }
    }

    static byte[] file(int format, int division, Track... tracks) {
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        o.writeBytes(new byte[] {'M', 'T', 'h', 'd', 0, 0, 0, 6, 0, (byte) format, 0, (byte) tracks.length,
            (byte) (division >> 8), (byte) division});
        for (Track t : tracks) {
            byte[] b = t.bytes();
            o.writeBytes(new byte[] {'M', 'T', 'r', 'k', (byte) (b.length >> 24), (byte) (b.length >> 16), (byte) (b.length >> 8), (byte) b.length});
            o.writeBytes(b);
        }
        return o.toByteArray();
    }

    /** A C-major scale up and down in quarters at 100 BPM (format 0, 480 PPQN): 16 notes over 4 lanes. */
    static byte[] scale() {
        int[] p = {60, 62, 64, 65, 67, 69, 71, 72, 72, 71, 69, 67, 65, 64, 62, 60};
        Track t = new Track().tempo(0, 600_000);
        for (int x : p) {
            t.on(0, 0, x, 100).off(480, 0, x);
        }
        return file(0, 480, t.end());
    }
}
