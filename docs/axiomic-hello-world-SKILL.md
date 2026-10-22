---
name: axiomic-hello-world
description: Work with AxiomicCoreness/hello_world.py — φ-harmonic lattice, PEQS credit vault, Port 380 gate, K8s Layer 314, ledger seals, full digests (no truncation).
---

# AxiomicCoreness/hello_world.py

Public Sovereign Engine on GitHub `AxiomicCoreness/hello_world.py` (branch `main`).
The engine is dynamic, deterministic and nonstochastic: the same inputs and seed give the same trajectory.

Prefer **current `main` HEAD** over any pinned short SHA in older notes. Files exist even when GitHub code search returns empty — use path/filename or clone.

## When to Use

- Deploy Dashboard (Flask + HTMX → `peqs_vault`)
- Run Port 380 gate (stdlib HTTP on `:380`, Layer 314)
- Deploy Kubernetes (`garden` namespace)
- Ledger seals, Merkle roots, collision defense, timesecret
- φ-harmonic math anchors, Q8.24 / hybrid RK4, tokenizer `struct '>q'`
- Digests must be **full 64-hex** (SHA-256) or **128-hex** (SHA-512); never `[:16]` ellipsis
- Run TeaVM Rhythm Game (Java-to-JS Connectome autoplay)
- Validate HHMI Connectome XML against XSD (XXE hardened)
- Verify Float Safety (`math.isclose`)

## Quick Start — Three Surfaces

| Surface | Command | Role |
|---------|---------|------|
| Dashboard | `PYTHONPATH=. python3 -m peqs_vault.app` | Flask + HTMX → credit_vault |
| Port 380 | `python3 run_port380.py` | HTTP `:380` Layer 314 + ternary gate |
| K8s | `bash quantum/install_k8s.sh` | ns `garden` + ConfigMap + Deploy/Svc/Ingress |

```bash
git clone https://github.com/AxiomicCoreness/hello_world.py.git && cd hello_world.py
git checkout main
pip install flask   # for dashboard only
PYTHONPATH=. python3 -m peqs_vault.app
python3 run_port380.py
bash quantum/install_k8s.sh
