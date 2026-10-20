#!/usr/bin/env python3
"""Write a metronome click track as a mono 16-bit PCM WAV, optionally an .ogg.

Same samples as logic/ClickTrack.java (the page synthesises its own copy, so
nothing binary is committed). Beat k starts at sample round(k * rate * 60 / bpm);
tb is the time since *that beat's* start, so every click has the same shape.
(Computing a decay from song time instead, e.g. ``-t % 0.05``, parses as
``(-t) % 0.05`` in Python and gives a wrong click on every beat.)

Usage:
  python3 tools/gen_click_track.py                         # click_120bpm.wav, 4.5 s, 8 kHz
  python3 tools/gen_click_track.py --bpm 120 --ms 4500 --ogg   # also click_120bpm.ogg via ffmpeg
Then play it with ?chart=charts/sample_chart.json&audio=click_120bpm.ogg
(paths are relative to the page).
"""
import argparse
import math
import shutil
import struct
import subprocess
import sys
import wave

CLICK_S = 0.030
DECAY_S = 0.008
AMPLITUDE = 0.6 * 32767.0
ACCENT_HZ = 1500.0
BEAT_HZ = 1000.0


def java_round(x):
    """Math.round: floor(x + 0.5)."""
    return math.floor(x + 0.5)


def beat_start(k, bpm, rate):
    return java_round(k * rate * 60.0 / bpm)


def samples(bpm, duration_ms, rate):
    n = duration_ms * rate // 1000
    out = [0] * n
    k, start, nxt = 0, 0, beat_start(1, bpm, rate)
    for i in range(n):
        while i >= nxt:
            k += 1
            start = nxt
            nxt = beat_start(k + 1, bpm, rate)
        tb = (i - start) / rate
        if tb < CLICK_S:
            f = ACCENT_HZ if k % 4 == 0 else BEAT_HZ
            v = AMPLITUDE * math.exp(-tb / DECAY_S) * math.sin(2.0 * math.pi * f * tb)
            out[i] = java_round(v)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bpm", type=float, default=120.0)
    ap.add_argument("--ms", type=int, default=4500, help="length in ms (default 4500)")
    ap.add_argument("--rate", type=int, default=8000, help="sample rate (default 8000)")
    ap.add_argument("--out", default=None, help="output .wav (default click_<bpm>bpm.wav)")
    ap.add_argument("--ogg", action="store_true", help="also convert to .ogg (Vorbis) with ffmpeg")
    a = ap.parse_args()
    out = a.out or "click_%gbpm.wav" % a.bpm
    pcm = samples(a.bpm, a.ms, a.rate)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(a.rate)
        w.writeframes(struct.pack("<%dh" % len(pcm), *pcm))
    print("wrote %s (%d samples, %d Hz, %.3f s)" % (out, len(pcm), a.rate, len(pcm) / a.rate))
    if a.ogg:
        if shutil.which("ffmpeg") is None:
            sys.exit("ffmpeg not found; the .wav works in browsers as-is")
        ogg = out[:-4] + ".ogg" if out.endswith(".wav") else out + ".ogg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-ac", "1",
                        "-c:a", "libvorbis", "-q:a", "0", ogg], check=True)
        print("wrote %s" % ogg)


if __name__ == "__main__":
    main()
