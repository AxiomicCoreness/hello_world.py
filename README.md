# AxiomicCoreness

AxiomicCoreness is a mixed-language repository centered on a φ-harmonic
"sovereign brain" engine. It pairs a Python sovereign engine with a Java
17 / Maven simulation sidecar, a FastAPI service, and a set of verification
gates that keep the φ-invariants honest.

## Layout

The repository is built around `sovereign/engine.py` — the full sovereign
engine (options 0-60, seal handler, φ-predictor daemon, witness storage,
HTTP server). Every other module wires against it.

```
AxiomicCoreness/
├── sovereign/ ← φ-harmonic core (Python)
│   ├── engine.py ← THE ENGINE — scripts/ml_sovereign_core.py
│   ├── kernel.py ← adjudication kernel (wired_kernel) — K1-K7 gates
│   ├── octonion_table.py ← Fano-plane octonion multiplication table
│   ├── phi_mod_mean.py ← φ recomputed from x² − x − 1 = 0, asserted
│   ├── aklt_e2e.py ← AKLT invariant gates G1-G10
│   └── __init__.py ← package entry (dependency-light)
│
├── quantum/cdp_convergence/ ← CDP convergence package (WebSocket gate, OAuth2)
├── quantum/cordis_bridge/ ← Cordis bridge package
│
├── app/ ← FastAPI service (app.main:app, port 8000)
├── port380_mcp.py ← /mcp/tool → Java SovereignMain bridge (port 380)
├── .container/ ← stdlib container app + supervisor (port 380)
│
├── src/main/java/com/fruitfly/brain/ ← Java 17 simulation sidecar
│   ├── SovereignMain.java
│   ├── SovereignConstants.java
│   ├── WarriorQuadratic.java ← seed polynomial x² − x − 1 = 0
│   ├── LIFRK4.java
│   ├── Connectome.java
│   └── ...
├── src/test/java/com/fruitfly/brain/ ← JUnit 5 tests
│   ├── WarriorQuadraticTest.java
│   ├── KaTeXMacroSetTest.java
│   └── ...
│
├── scripts/ ← operational scripts
│   ├── build.sh ← Maven jar build
│   ├── run-simulation.sh ← run the Sovereign Brain jar
│   ├── lint.sh ← one-surface lint gate
│   ├── link_core.sh ← symlink .container/ at the sovereign engine
│   └── ...
│
├── tests/ ← pytest suite
├── workflows/ ← CI + deploy, AKLT e2e
├── .github/workflows/ ← python-package CI
├── docs/ ← architecture, KaTeX macros, schema
├── pom.xml ← Maven build for the Java sidecar
└── requirements.txt ← Python dependencies
```

## Dependency wiring

```
sovereign/engine.py ──φ²──> kernel.py, octonion_table.py, phi_mod_mean.py, aklt_e2e.py
│
▼
port380_mcp.py ──java──> com.fruitfly.brain.SovereignMain (src/main/java)
│
▼
app/ (FastAPI) ── healthz, /oidc_handover, /restart
```

The seed polynomial feeds the trimer, which feeds the automaton:

```
WarriorQuadratic.positiveRoot() === SovereignConstants.PHI (verified)
WarriorQuadratic.negativeRoot() === −SovereignConstants.PHI_INV (verified)
DarkStateInvariant λ₂ = 1, absorbing
```

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The interactive API docs live at http://127.0.0.1:8000/docs.

### Run the sovereign engine

```bash
python3 sovereign/engine.py [--serve|--full|--menu|--show-state|--ingress|--sovereignty|--pulse]
```

### Run verification gates

```bash
python3 sovereign/kernel.py # K1-K7 adjudication kernel self-test
python3 sovereign/phi_mod_mean.py # φ recomputed from x² − x − 1 = 0
python3 sovereign/aklt_e2e.py # AKLT invariant gates G1-G10
python3 sovereign/octonion_table.py # Fano-plane octonion table
```

### Build and run the Java sidecar

```bash
./scripts/build.sh
./scripts/run-simulation.sh
```

### Lint gate

```bash
./scripts/lint.sh
```

Runs Maven tests, Python compilation, and the kernel self-test, then
appends a fixed-form lint block to `notes_to_kernel.md` and pipes the
summary through `sovereign/kernel.py` adjudication.

## Running tests

```bash
pytest # Python suite
mvn -B test # Java sidecar (JDK 17)
```

## Services

Two services run from one image (see `docker-compose.yml`):

| Service     | Port | Command                           |
| ----------- | ---- | --------------------------------- |
| FastAPI app | 8000 | `python3 -m uvicorn app.main:app` |
| MCP bridge  | 380  | `python3 port380_mcp.py`          |

`GARDEN_SECRET` must be exported in the shell or placed in a sibling
`.env` file.

## Container

`.container/` holds a stdlib-only HTTP service plus a process
supervisor. No third-party dependencies. See `.container/README.md` for
write surfaces, environment, and restart semantics.
