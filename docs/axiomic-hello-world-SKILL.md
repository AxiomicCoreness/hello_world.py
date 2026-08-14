---
name: axiomic-hello-world
description: Work with AxiomicCoreness/hello_world.py — φ-harmonic lattice, PEQS credit vault, Port 380 gate, K8s Layer 314, ledger seals, full digests (no truncation).
---

# AxiomicCoreness/hello_world.py

Public Sovereign Engine on GitHub `AxiomicCoreness/hello_world.py` (branch `main`).

Prefer **current `main` HEAD** over any pinned short SHA in older notes. Files exist even when GitHub code search returns empty — use path/filename or clone.

## When to Use

- Deploy Dashboard (Flask + HTMX → `peqs_vault`)
- Run Port 380 gate (stdlib HTTP on `:380`, Layer 314)
- Deploy Kubernetes (`garden` namespace)
- Ledger seals, Merkle roots, collision defense, timesecret
- φ-harmonic math anchors, Q8.24 / hybrid RK4, tokenizer `struct '>q'`
- Digests must be **full 64-hex** (SHA-256) or **128-hex** (SHA-512); never `[:16]` ellipsis

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
```

## Components

### Dashboard — `peqs_vault/app.py`
Flask + HTMX bridge to credit vault; φ-harmonic fee paths.

### Port 380 — `run_port380.py` → `quantum/port_380_http.py`
- GET `/health`, `/status`, `/380`; POST `/gate`
- Ternary scaling: `python3 quantum/port_380_gate.py --ternary {-1,0,1}`
- Layer 314 anchors (full hex):
  - Anchor: `8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d`
  - Leaf: `807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68`

### Kubernetes — `bash quantum/install_k8s.sh`
- Namespace `garden`
- Manifests under `k8s/` including `deployment-port-380.yaml`, `service-port-380.yaml`, `ingress.yaml`
- `kubectl get all -n garden`

## Math Anchors

| Symbol | Value |
|--------|--------|
| φ | (1+√5)/2 |
| Phase lock | 202.6° |
| Breath | 71.975 Hz |
| Pauli trace | φ⁻² ≈ 0.38196601125 |
| Crypto | AES-256 + SHA3-512 (no AES-512) |
| Tokenizer wire | `struct.pack('>q')` — 8-byte signed BE |

## Policies (hard)

1. **Append-only ledger** — do not re-seal existing `entry_index`.
2. **Full digests** — no `[:16]` / `[:32]` fingerprint truncation in code or seals.
3. **Narrative Merkle strings** (`g8a9…`, `s0f1…`, letters beyond `f`) are labels, not SHA-256.
4. **Collision defense** — repeated historical transmissions are informational only.
5. Domain-separated roots for Layer 326+: `GARDEN.LAYER{N}.MERKLE.v1 ‖ 0x00 ‖ canonical_json`.

## Key Paths

- `golden_ratio.py`, `sovereign_hamiltonian.py`, `quantum/symplectic_time_origami.py`
- `hybrid_rk4_simulator.py`, `tests/test_hybrid_rk4.py`
- `quantum/tokenizer_binary.py`, `quantum/no_truncation_policy.py`
- `ledger/*.yaml` (e.g. 8746–8750, 8766–8767)
- `quantum/genesis_co_create.py`

## Troubleshooting

- `ModuleNotFoundError: peqs_vault` → `PYTHONPATH=. python3 -m peqs_vault.app`
- Missing flask → `pip install flask`
- Port 380 busy → `lsof -i :380`
- Empty GitHub code search → clone or raw path; files are on `main`
