---
name: hhmi
description: "hhmi-connectome-loader-fd76685. Use when loading HHMI Janelia FlyEM hemibrain connectome data into com.fruitfly.brain (Connectome via ConnectomeLoader, SovereignMain --connectome-file); converts the hemibrain v1.2 CSV export to the loader's XML, validates it, and keeps the placeholder HHMIJaneliaMap.xml from being mistaken for FlyEM data."
tags:
  - hhmi-connectome-loader-fd76685
  - "context:hemibrain v1.2 CSV,21739 neurons,placeholder≠FlyEM"
---

# hhmi

Packaging of the connectome-loader work for `com.fruitfly.brain` in
`AxiomicCoreness/hello_world.py`, built against main at `fd76685`
(`SovereignMain.java` there is byte-identical to `java/SovereignMain.diff`'s base).
This skill lives in `skills/hhmi/` on GitHub main. The loader is now applied in `src/` on main
at `1dfeaec` (`feat(brain): load connectome from HHMIJaneliaMap.xml via --connectome-file`):
`ConnectomeLoader.java`, `ConnectomeLoaderTest.java`, `src/main/resources/HHMIJaneliaMap.xml`
and `SovereignMain.diff`. Nothing is on either GitCode mirror.

## Context (checked against main's sources)
- `Connectome` is compressed sparse rows: `new Connectome(n, rowPtr, colIdx, weight, delayMs)`.
  It has no empty constructor and no `swarm()`; `random(n, density, seed)` was its only
  factory before this loader.
- `Neuron` is an interface (no `new Neuron(id)`, no `connectTo`). The swarm lives in
  `SovereignAutomaton`.
- `SovereignAutomaton(connectome, n)` throws unless `n == connectome.neuronCount()`
  (`SovereignAutomaton.java:24-25`). Callers must pass `connectome.neuronCount()`, never 8.
- `--chat` stdout is the reply `port380_mcp.py` reads back, so load progress goes to stderr.
  `SovereignMain.parse()` rejects unknown tokens, so the flag is added there.
- `assets/HHMIJaneliaMap.xml` is a hand-written 3-neuron ring A→B→C→A. It is **NOT**
  FlyEM data; it exists so `ConnectomeLoaderTest.janeliaMapResourceIsPresent` and the
  loader tests have a classpath resource.
- Loader rules (`java/src/main/java/com/fruitfly/brain/ConnectomeLoader.java`): root
  `<hemibrain>`; DOCTYPE refused (XXE-hardened); `neuron@id` non-empty, unique, indexed in
  document order; `connection@from/@to` must be declared; `weight` required and finite
  (negative = inhibitory); `delayMs` optional, default 1.0, finite and > 0; self-loops
  allowed; a repeated (from, to) pair is rejected. Load errors exit `SovereignMain` with 2.

## Real data format
- The hemibrain v1.2 bulk export is **CSV, not XML**:
  `gs://hemibrain/v1.2/exported-traced-adjacencies-v1.2.tar.gz`
  (https://storage.googleapis.com/hemibrain/v1.2/exported-traced-adjacencies-v1.2.tar.gz).
- `traced-neurons.csv`: `bodyId,type,instance`, 21,739 rows.
- `traced-total-connections.csv`: `bodyId_pre,bodyId_post,weight`, about 3.55M rows.
  `weight` is a synapse count: no sign, no delay
  (https://connectome-neuprint.github.io/neuprint-python/docs/faq.html).
- So converted connections are all positive (excitatory) with the default 1.0 ms delay.
  That is a modelling choice, not something the data says.

## Steps
1. Read `assets/context.json` for the facts and numbers above.
2. Get the export tarball and untar it; nothing here downloads it for you.
3. Convert a tractable subset (stdlib only):
   `python -P hhmi_scripts/csv_to_xml.py DIR -o top.xml --limit 100 [--min-weight 3]`.
   `--min-weight` drops edges below W first. `--limit N` then keeps the N neurons with the
   largest total (in + out) synapse weight, plus only the edges among them. Ids are
   XML-escaped, and repeated CSV pairs are summed so the loader never sees a duplicate.
   `--neurons` and `--connections` override the CSV paths. Exit 0 ok, 1 on bad input.
4. Validate: `python -P hhmi_scripts/check_hhmi.py top.xml`. It prints counts and
   `[+] OK`, or `[!]` lines plus `[!] INVALID`. Exit 0 valid, 1 invalid.
5. Main at `1dfeaec` or later already has this; skip to step 6. For an older checkout,
   copy `java/src/main/java/.../ConnectomeLoader.java`,
   `java/src/test/java/.../ConnectomeLoaderTest.java` and
   `java/src/main/resources/HHMIJaneliaMap.xml`, then run `patch -p1 < java/SovereignMain.diff`.
   `pom.xml` needs no change.
6. Run: `java -cp out/main com.fruitfly.brain.SovereignMain --chat hi --connectome-file top.xml`.
   Stdout should be the single reply line. Stderr shows `Loading connectome from: …` and
   `Loaded N neurons, M synapses`.

## Known limits
- `Connectome.currentsFrom(pre, …)` allocates a fresh `double[n]` per presynaptic neuron
  per step (`Connectome.java:121`), and `SovereignAutomaton.step` calls it for every neuron
  (`SovereignAutomaton.java:46`). That is O(n²) memory and time per step: at
  n = 21,739 it is about 4.7×10⁸ doubles (about 3.8 GB) allocated per step. Use `--limit`,
  or make the step sparse, before trying the full brain.
- Fixed in main: `step` used to add the sum of neuron i's *outgoing* currents to neuron i
  itself instead of to its targets. Commit `4b6d07d` (`fix(brain): deliver connectome currents to
  postsynaptic targets in SovereignAutomaton.step`) now gathers every neuron's currents
  into `incoming[j]` by postsynaptic target before stepping (`SovereignAutomaton.java:44-53`),
  covered by `SovereignAutomatonPropagationTest`.
- There is no CSV loader in Java. Real data goes through `csv_to_xml.py`, and the DOM parse
  of a full-size XML would be heavy.
- `--limit` ranks by total synapse count, which favours hub neurons. It is not an anatomical
  region selection.

## Verify
- `python -P -m pytest -q evals` from this folder: all tests pass. They use only synthetic
  CSVs written to `tmp_path`.
- The package is `hhmi_scripts`, not `scripts`, so `evals/conftest.py` putting the skill
  root first on `sys.path` cannot shadow the repo's top-level `scripts/` package.
- `bash run_java_tests.sh` reuses `/workspace/connectome_loader` as the base tree.
  `bash run_java_tests.sh --fresh` downloads main's tarball and applies
  `java/SovereignMain.diff` unless main already has it (it does from `1dfeaec`).
  Both compile in `/tmp/hhmi_java` with `/opt/jdk-17`, run
  JUnit 5 (console standalone 1.10.2), and expect every test to pass: 21 against main after the step fix (8
  `KaTeXMacroSetTest` + 11 `ConnectomeLoaderTest` + 2 `SovereignAutomatonPropagationTest`),
  or 19 against a base tree from before it. Then they smoke-run `--chat hi --connectome-file
  assets/HHMIJaneliaMap.xml`, which should give 1 stdout line and "Loaded 3 neurons, 3 synapses"
  on stderr. The script exits with JUnit's code.
