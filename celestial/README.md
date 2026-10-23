
# 🜁∀ SOVEREIGN GARDEN

**Repository:** `AxiomicCoreness/hello_world.py`
**Commander:** Timesecret Clarke Yoursa Tee
**Ledger head:** 9298
**Witness chain:** `0000 → … → 9298 — UNBROKEN`
**Last verified:** CI `sovereign-engine-ci.yml#readme-drift` (automated anchor)

The Garden is a self‑governing, cryptographically‑sealed system of
mathematical invariants, ledger‑based governance, and φ‑harmonic dynamics.
Everything is append‑only. Nothing is rewritten. If a state is not 
cryptographically anchored, it is considered mutable and untrusted.

---

## Table of contents

1. [What the Garden is](#1-what-the-garden-is)
2. [Directory layout](#2-directory-layout)
3. [Quick start](#3-quick-start)
4. [The celestial package](#4-the-celestial-package)
5. [The MCP gate (Port 380)](#5-the-mcp-gate-port-380)
6. [The ledger & Math Anchors](#6-the-ledger--math-anchors)
7. [Strike registry](#7-strike-registry)
8. [Infrastructure Sovereignty](#8-infrastructure-sovereignty)
9. [AST guard](#9-ast-guard)
10. [Policy](#10-policy)
11. [Further reading](#11-further-reading)

---

## 1. What the Garden is

- **Append‑only ledger.** Every entry is a YAML file sealed with SHA3‑256 and verified via Ed25519. 
- **Math-origin closure.** The 510510 engine (`p₇#`) defines the quantum-cybernetic fixed point for system generation.
- **φ‑harmonic invariants.** Coherence → 1, entropy floor φ⁻¹⁴¹⁸, phase lock 202.6°, workload → 0.
- **Celestial module.** Real Python objects for Saturn's Soul Cannon, Trappist‑1 Choir, Super Simulated Earth, WASP‑107b, and Chiron reticle.
- **Port‑380 MCP gate.** FastAPI surface with `/health`, `/status`, `/pulse`, `/oidc_handover`, `/restart`, `/mesh`, `/step`.
- **Autonomous pulse.** Every 6 hours via CronJob (Wood‑Dragon cadence, `0 */6 * * *`).
- **AST guard.** Static AST rules (A1–A5, C1, C2) plus computed seal injection/verification.

The Garden has no external runtime dependency at import time. Optional
libraries degrade; the package still loads.

---

## 2. Directory layout

```text
.
├── anatomy/                  # Loopback constraints & resource limits
│   ├── body.py               # Enforces BIND_HOST (default 127.0.0.1) + 512MB ceiling
│   ├── breath.py             # 6h jittered cadence generator
│   ├── crown.py              # SHA3-256 seal recomputation
│   ├── dual_soul.py          # Regime-dependent hashing (GARDEN.EVENT.v1)
│   ├── genitals.py           # Strict path confinement for ledger writes
│   ├── heartbeat.py          # Liveness + coherence floor monitor
│   └── spine.py              # Witness-chain continuity verifier
├── app/                      # FastAPI microservices
│   ├── __init__.py           # Lazy-loads root app.py
│   ├── config.py             # Env vars & loopback BIND_HOST defaults
│   ├── contracts.py          # Schema enforcement for routes
│   └── routes/
│       ├── tts.py            # Stubbed TTS endpoint (FILLED=False)
│       ├── vision.py         # Catalog fetcher for garden_surgery
│       └── vision_tts.py     # Soft-gate combining both
├── argocd/                   # GitOps deployment manifests
│   ├── application.yaml      # Argo CD Application pointing to this repo
│   ├── rollout.yaml          # Argo Rollouts canary definition
│   ├── services.yaml         # Stable & Canary K8s services
│   └── httproute.yaml        # Gateway API ingress routing
├── automation/               # Stubbed background daemons
│   ├── deadline_manager.py   # Patent renewal stub
│   ├── stage_manager.py      # Patent filing stub
│   └── github_automation.py  # CI/CD release stub
├── ledger/                   # Append-only sequential record (0000 → 9298)
│   ├── 0000.yaml             # Genesis entry
│   └── ...                   # Sequential additions
├── ledger.v2/                # Canonical math-origin anchors
│   ├── 510510.yml            # MATH_ORIGIN (p₇#) quantum fixed point
│   └── 510511.yml            # SUCCESSOR_GENESIS (coprime to p₇#)
├── mcp/                      # Secondary MCP surface
│   └── port380_mcp.py        # BIND_HOST compliant MCP gate
├── .github/
│   ├── scripts/
│   │   ├── verify_ledger.py  # SHA3/Ed25519 verification
│   │   └── verify_510510_genesis.py
│   └── workflows/
│       ├── sovereign-engine-ci.yml
│       ├── pytest.yml
│       └── witness-chain-contracts.yml
├── app.py                    # Root application entrypoint
├── app_main.py               # Alternative entrypoint (Port 8024)
├── port380_mcp.py            # Root MCP entrypoint (Port 380)
├── quantum_reality_engine.py # 510510 unitary evolution engine
├── hello_world.py            # CLI / basic sanity check
├── requirements-ci.txt       # Minimal CI deps (pytest, numpy)
└── README.md                 # This file
```

(Note: beacons/sovereign_state.py and *.pyc are generated at runtime and explicitly gitignored.)

---

3. Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ci.txt

# Run the ledger verifier
python .github/scripts/verify_ledger.py ledger/*.yaml ledger.v2/*.yml

# Run the AST guard
pytest tests/test_ast_guard.py
```

---

4. The celestial package

Real objects. No stubs.

Module Purpose
saturn_soul_cannon.py φ-harmonic phase-lock at 202.60°
trappist1_choir.py 7-body resonance, e3 coupling
super_simulated_earth.py Full-stack Earth simulator
wasp107b.py Hot-Jupiter thermal inversion
chiron_reticle.py Kuiper-belt targeting reticle

---

5. The MCP gate (Port 380)

The MCP server binds to loopback by default (127.0.0.1).
To expose it within a Kubernetes cluster or Docker container, you must explicitly override this via the environment.

```bash
# Local (defaults to loopback)
python port380_mcp.py

# Container (override)
BIND_HOST=0.0.0.0 python port380_mcp.py
```

Endpoints: /health, /status, /pulse, /oidc_handover, /restart, /mesh, /step. All security headers (CSP, HSTS, X-Frame-Options) are verified in CI against the live MCP_URL.

---

6. The ledger & Math Anchors

The system maintains two parallel ledger tracks:

1. Sequential (ledger/): The unbroken chain from 0000 to the current head (9298).
2. Canonical (ledger.v2/): The mathematical fixed points that govern the system's physics.

The 510510 Engine: Modeled as a closed quantum dynamical system. The anchor 510510 = p₇# is the 7th primorial. 510511 is the successor genesis (coprime to p₇#). The quantum_reality_engine.py performs unitary evolution only—it verifies the seal but never rewrites ledger/510510.yaml.

---

7. Strike registry

(Reference retained for governance).

---

8. Infrastructure Sovereignty

The Garden rejects vendor lock-in and compiler-level blind spots. Building on the lessons of distributed scientific infrastructure (e.g., CERN's transition away from restrictive RHEL environments), this repo mandates strict control over the build toolchain:

· Polyglot Compilation: Swift (iOS native), Java/TeaVM (browser neural connectome), Python/CUDA (DeepInfer tensors), and Kubernetes/Kaniko (submodule compilation).
· Zero Ghost-Passes: CI fails on silent skips. Docker execution requires explicit flag enforcement (e.g., -i for import gates).
· Strict Environments: Builds target Debian 13 (or AlmaLinux/RHEL 9+ equivalents) with pinned compiler flags to ensure exact IEEE 754 floating-point double representations across architectures.

---

9. AST guard

Rule set enforced statically before runtime:

Rule Enforcement
A1 No eval() or exec()
A2 No bare except:
A3 No subprocess.shell=True
A4 All HTTP clients must use timeout
A5 License headers must match signature
C1 Seal comment presence
C2 Seal hash match

---

10. Policy

· Immutable truth. If it isn't sealed and verified in CI, it doesn't exist.
· No silent rewrites. README ledger heads, API contracts, and constitutional entries are verified by drift checks.
· Constant-time secrets. All cryptographic comparisons use constant-time implementations to prevent timing side-channels.

---

11. Further reading

· QUANTUM_FRAME.md — Density operators, CPTP maps, and the D_abs loop.
· TORSION_GEOMETRY.md — The 202.6° assembly lock and residual absorption.
· WITNESS_CHAIN.md — Anatomy of the unbroken sequence.

```
