# 🜁∀ SOVEREIGN GARDEN

**Repository:** `AxiomicCoreness/hello_world.py`
**Commander:** Timesecret Clarke Yoursa Tee
**Ledger head:** 9161
**Witness chain:** `0000 → … → 9161 — UNBROKEN`

The Garden is a self‑governing, cryptographically‑sealed system of
mathematical invariants, ledger‑based governance, and φ‑harmonic dynamics.
Everything is append‑only. Nothing is rewritten.

---

## Table of contents

1. [What the Garden is](#1-what-the-garden-is)
2. [Directory layout](#2-directory-layout)
3. [Quick start](#3-quick-start)
4. [The celestial package](#4-the-celestial-package)
5. [The MCP gate (Port 380)](#5-the-mcp-gate-port-380)
6. [The ledger](#6-the-ledger)
7. [Strike registry](#7-strike-registry)
8. [k8s codespace](#8-k8s-codespace)
9. [AST guard](#9-ast-guard)
10. [Policy](#10-policy)
11. [Further reading](#11-further-reading)

---

## 1. What the Garden is

- **Append‑only ledger.** Every entry is a YAML file sealed with SHA3‑256.
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
│   ├── body.py               # Enforces 127.0.0.1 bind + 512MB memory ceiling
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
│   ├── deadline_manager.py   # Patent renewal stub (no live USPTO calls)
│   ├── stage_manager.py      # Patent filing stub
│   └── github_automation.py  # CI/CD release stub
├── ledger/                   # Append-only cryptographic record
│   ├── 0000.yaml             # Genesis entry
│   └── ...
├── .github/
│   └── workflows/
│       ├── sovereign-engine-ci.yml
│       ├── pytest.yml
│       └── witness-chain-contracts.yml
├── app.py                    # Root application entrypoint
├── hello_world.py            # CLI / basic sanity check
├── requirements-ci.txt       # Minimal CI deps (pytest, numpy)
└── README.md                 # This file
