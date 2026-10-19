# AxiomicCoreness/hello_world.py — sovereign_engine_V5

![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23378305.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Developed by Clarke Yoursa Tee, AxiomicCoreness is a public MIT-licensed sovereign computational engine for φ-harmonic ledger verification. It features a Dual ASGI control plane (FastAPI + Pydantic), a Java 17 simulation sidecar, and runtime verification gates that enforce the dark-state invariant λ₂ = 1.

**Keywords:** sovereign-engine, fastapi, pydantic, asgi, fastmcp, ledger-verification, zenodo-archive, reproducible-research, python, mit-license

## Layout

The repository is built around `sovereign/engine.py` — the full sovereign engine (options 0-60, seal handler, φ-predictor daemon, witness storage, HTTP server). Every other module wires against it.

```text
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
├── port380_mcp.py ← FastAPI gate: /health(z), /gate, X-Garden-Secret /pulse + /mcp/tool (Python only; PORT default 380, host 127.0.0.1)
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
