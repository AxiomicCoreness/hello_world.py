# teavm-rhythm

A small Beat-Saber-style 2D rhythm game for the browser, written in Java and
compiled to JavaScript with [TeaVM](https://teavm.org) 0.10.2.

Notes fall down four lanes. Hit **D F J K** as each note crosses the line.

This is a **standalone Maven project**. It isn't a module of the root
`pom.xml`, so the root `sovereign-brain` build and the `java-maven-test.yml`
workflow (which watches the repo-root `src/**` and `pom.xml`) don't see it.

## Layout

| Path | What it is |
|---|---|
| `src/main/java/com/fruitfly/games/rhythm/logic/` | Pure game rules: `Note`, `Judgement`, `NoteChart`, `RhythmGame`. JDK only, with no TeaVM or JSO imports (`LogicPurityTest` enforces this). |
| `src/main/java/com/fruitfly/games/rhythm/web/Main.java` | Browser layer: TeaVM JSO canvas drawing, `keydown` input and the `requestAnimationFrame` loop. |
| `src/main/webapp/index.html` | Page that loads `classes.js` and calls `main()`. |
| `src/test/java/.../logic/` | JUnit 5 tests for hit windows, scoring, combo reset and chart determinism. |
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

## Build

JDK 17 and Maven 3.9 are needed. Run these from this directory
(`games/teavm-rhythm/`):

```bash
mvn -B test        # 33 JUnit tests for the logic
mvn -B package     # tests, then TeaVM compile -> target/webapp/{index.html,classes.js}
node --check target/webapp/classes.js
node tools/smoke.js   # boots classes.js headless, plays 3 notes, checks the HUD
```

## Run

```bash
cd target/webapp
python3 -m http.server 8000
# open http://localhost:8000/            (default seed 2026)
# open http://localhost:8000/?seed=123   (any other fixed chart)
```

Press **Space** to start, **D F J K** to hit, **R** to restart and **N** for
a new seed (on the title screen).
