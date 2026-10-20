# teavm-rhythm

A small Beat-Saber-style 2D rhythm game for the browser, written in Java and
compiled to JavaScript with [TeaVM](https://teavm.org) 0.10.2.

Notes fall down four lanes. Hit **D F J K** as each note crosses the line,
or press **B** to let a four-neuron LIF "fly brain" autoplayer play.

This is a **standalone Maven project**. It isn't a module of the root
`pom.xml`, so the root `sovereign-brain` build and the `java-maven-test.yml`
workflow (which watches the repo-root `src/**` and `pom.xml`) don't see it.

## Layout

| Path | What it is |
|---|---|
| `src/main/java/com/fruitfly/games/rhythm/logic/` | Pure game rules: `Note`, `Judgement`, `NoteChart`, `RhythmGame`, the autoplayer `LifNeuron` and `LifAutoplayer`, the JSON chart loader `ChartJson` / `LoadedChart` / `ChartFormatException`, the `SongClock` and the `ClickTrack` synthesiser. JDK only, with no TeaVM or JSO imports (`LogicPurityTest` enforces this). |
| `src/main/java/com/fruitfly/games/rhythm/web/Main.java` | Browser layer: TeaVM JSO canvas drawing, `keydown` input, the `requestAnimationFrame` loop and chart fetching (`XMLHttpRequest`). |
| `src/main/java/com/fruitfly/games/rhythm/web/AudioSync.java` | Wraps one HTML5 `<audio>` element as the song clock source. |
| `src/main/webapp/index.html` | Page that loads `classes.js`, calls `main()`, and shows the scoring formulas in KaTeX 0.16.11 (CDN, pinned with SRI hashes; plain-text fallback if it can't load). |
| `src/main/webapp/charts/sample_chart.json` | Sample 6-note chart, "Fruit Fly Heartbeat". |
| `src/test/java/.../logic/` | JUnit 5 tests (74) for hit windows, scoring, combo reset, chart determinism, the LIF port, its parity with the real `LIFRK4`, the autoplayer, the JSON loader, the song clock and the click track. |
| `tools/gen_click_track.py` | Writes the same click track as a `.wav` (and `.ogg` with `--ogg`, via ffmpeg) for use outside the page. |
| `src/test/resources/lif_rk4_golden_traces.txt` | Golden v / g / refractory / spike traces generated from the real root `LIFRK4`. Do not hand-edit. |
| `tools/LifGoldenTraceGen.java`, `tools/regen-lif-traces.sh` | Trace generator. It compiles against the root `src/` LIFRK4 and isn't part of the Maven build. |
| `tools/smoke.js` | Headless Node smoke test for the compiled `classes.js`, using a stubbed DOM. |

## Rules

- **Hit windows** (|press − note|, inclusive): PERFECT ≤ 50 ms (300),
  GREAT ≤ 100 ms (200), GOOD ≤ 150 ms (100). A note more than 150 ms late
  becomes a MISS.
- A press with no note in range in that lane is ignored. It has no penalty.
- **Score per hit** = base × multiplier. The multiplier is
  `min(4, 1 + combo / 10)`, using the combo before the hit.
- A MISS resets the combo to 0. Max combo, counts and accuracy are shown at
  the end.
- **Chart**: `NoteChart.generate(seed, 64, 120 bpm, 2000 ms lead-in)` uses its
  own 64-bit LCG, not `java.util.Random`, so a seed gives the same chart on the
  JVM and in the compiled JS. Steps are half or whole beats. No lane repeats
  more than twice in a row.

## LIF autoplayer (key B)

`LifNeuron` is a port of the root project's
`src/main/java/com/fruitfly/brain/LIFRK4.java` at `fca08122` (blob
`44ded4a3`). It's copied, not imported, because this project is standalone and
can't depend on `com.fruitfly.brain`. It mirrors:

- every constant, including the unused `SYNAPTIC_GAIN` (V_rest −52,
  V_thresh −45, V_reset −52 mV, τ_v 20 ms, τ_g 5 ms, 2.2 ms refractory, 50 ms
  tick, 50 substeps);
- RK4 on (v, g), with v held at V_reset while refractory;
- the threshold check after **every** 1 ms substep;
- `stepTick(double[])`, where input s is added to g at the start of substep s,
  and the legacy `stepTick(double)`, where input is added after the tick;
- the refractory countdown and clamp, including its rounding: 2.2 − 1 − 1 is
  0.20000000000000018, which the next substep clamps to 0.

`LifAutoplayer` runs one neuron per lane. When the song clock reaches
`noteTime − latency`, that lane's next note sends the neuron one conductance
pulse of G = 60. A spike in any substep is a key press in that lane at that
substep's time. Nothing else presses keys. The latency (3 ms) is measured from
a fresh neuron, not hard-coded. From rest a pulse G peaks at about 0.1575·G mV,
so anything under ~44.4 never fires. There's no randomness and no wall clock.
The result is the same at any frame rate.

Measured: for seed 2026 it hits 64/64 notes, all PERFECT, for a score of
58,800 and max combo 64. Seeds 1, 7, 42, 99 and 123456789 also hit at least
58/64 (the test threshold). B only switches between songs, so a score is
either all brain or all human.

### Parity with the real LIFRK4

`LifRk4ParityTest` replays six fixed input sequences through `LifNeuron` and
compares every substep's v, g and refractoryRemaining, and every spike
substep, to golden traces from the real `LIFRK4`, to 1e-12. It checks
4 ticks × 50 substeps × 6 traces = 1,200 states, with 15 spikes. It also checks
both `stepTick` APIs at tick boundaries and that the constants are exactly
equal.

The traces are in `src/test/resources/lif_rk4_golden_traces.txt` and are
written as exact hex doubles. `tools/LifGoldenTraceGen.java` makes them from
LIFRK4 itself. It reads per-substep state by calling LIFRK4's private
`substep` through reflection, and checks each tick bit for bit against a
second LIFRK4 driven only through the public `stepTick`. A 1e-11 change to v,
or to the refractory clamp, makes the test fail.

**When `LIFRK4.java` changes**, regenerate the traces and re-run the tests:

```bash
# from the repo root, JDK 17 on PATH
bash games/teavm-rhythm/tools/regen-lif-traces.sh
cd games/teavm-rhythm && mvn -B test
```

The script compiles the root `LIFRK4.java` together with the generator in a
temp directory. It writes the traces with a `source` line recording the commit
and blob. If `LifRk4ParityTest` then fails, update `LifNeuron` to match. Commit
the regenerated traces with the port change.

## JSON charts and audio sync

Open the page with `?chart=charts/sample_chart.json` (or any chart URL the
page can fetch). The format is:

```json
{
  "metadata": { "title": "Fruit Fly Heartbeat", "artist": "LIF Autoplayer", "bpm": 120, "offset_ms": 0 },
  "notes": [ { "time_ms": 1000, "lane": 0 }, { "time_ms": 1500, "lane": 0 } ]
}
```

`ChartJson.parse` is a small strict JSON parser in the logic package. It
checks that `title` and `artist` are strings, `bpm` is in (0, 1000],
`offset_ms` is an integer within ±600000, and every note has an integer
`time_ms` in [0, 86400000] and an integer `lane` 0–3. Notes may be in any
order; they're stably sorted by time. The same lane twice at the same time is
rejected. Unknown keys are ignored. An optional `metadata.audio` names an
audio file relative to the chart. Errors name the field, for example
`notes[1].lane: must be an integer 0..3, got 4`. The page shows the error and
keeps the generated chart.

The chart becomes an ordinary `NoteChart` (`NoteChart.fromNotes`), so the same
`RhythmGame` judges it with the same windows and scoring, and the B autoplayer
works unchanged.

**Clock.** With audio, song time is
`audio.currentTime × 1000 + offset_ms`. It's read as a double on every frame
and at every key press, and passed straight to `RhythmGame` (floored to whole
ms, so a note is never judged early). No per-frame deltas are summed, so
nothing drifts. A positive `offset_ms` makes notes due earlier against the
audio. If there's no audio, play() is refused, the audio errors or it ends,
`SongClock` falls back to the original frame clock, continuing from the last
audio reading. With no audio at all the game behaves exactly as before.

**Audio source**, in order: `?audio=URL`, then `metadata.audio`, then a click
track synthesised in the page by `ClickTrack` (mono 16-bit 8 kHz WAV as a
`data:` URI, at the chart's bpm, lasting until 1.5 s past the last note).
`?audio=none` turns audio off. `?audio=URL` without a chart puts the
generated seed chart on that audio's clock with offset 0.

No audio binary is committed. To get a file, run
`python3 tools/gen_click_track.py --ogg`. It writes `click_120bpm.wav`, which
is byte-identical to the page's track, and converts it to `click_120bpm.ogg`
(Vorbis) with ffmpeg. Put the file next to `index.html` and open
`?chart=charts/sample_chart.json&audio=click_120bpm.ogg`. The sample chart's
notes fall on beats 2–6 of the 120 bpm click.

## Lane labels

The lanes are labelled *antennal lobe*, *mushroom body*, *lateral horn* and
*lobula*. These are **display labels only**. The lanes aren't wired to those
regions, nothing reads the connectome, and the connectome schema is unchanged.

## Build

JDK 17 and Maven 3.9 are needed. Run these from this directory
(`games/teavm-rhythm/`):

```bash
mvn -B test        # 74 JUnit tests for the logic, including LIFRK4 parity
mvn -B package     # tests, then TeaVM compile -> target/webapp/{index.html,classes.js}
node --check target/webapp/classes.js
node tools/smoke.js   # boots classes.js headless: seed game + B-autoplay, then the JSON chart, audio clock and fallbacks
```

## Run

```bash
cd target/webapp
python3 -m http.server 8000
# open http://localhost:8000/            (default seed 2026)
# open http://localhost:8000/?seed=123   (any other fixed chart)
# open http://localhost:8000/?chart=charts/sample_chart.json   (JSON chart + synthesised click track)
```

Press **Space** to start, **D F J K** to hit, **R** to restart. On the title
or end screen, **B** toggles the autoplayer and **N** picks a new seed.

The KaTeX formulas need network access to cdn.jsdelivr.net. Offline, the page
shows the same formulas as plain text.
