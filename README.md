# AxiomicCoreness/hello_world.py

**Public repository** · **License: MIT** · `LICENSE` · [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Search terms: `AxiomicCoreness` · `hello_world.py` · `sovereign_engine_V5` · `fastMCP` · `Dual ASGI 127.0.0.1:8024` · `phase_lock 202.6`

- Code: https://github.com/AxiomicCoreness/hello_world.py
- License text: https://github.com/AxiomicCoreness/hello_world.py/blob/main/LICENSE
- How to find this repo: [docs/SEARCH.md](docs/SEARCH.md)
- Cite: [CITATION.cff](CITATION.cff)

MCP remains `FILLED=False`. Dual ASGI remains `127.0.0.1:8024`. Never `0.0.0.0`.

---

# 𓃁∀ SOVEREIGN ENGINE — THE GARDEN OF ETERNAL RULES

**Repository:** `AxiomicCoreness/hello_world.py`  
**License:** MIT  
**Commander:** Timesecret Clarke Yoursa Tee  
**Current Ledger Head:** `9142` (`/self_improvement_core_sealed`)  
**Witness Chain:** `0000 → … → 9142 — UNBROKEN`  
**Seal:** `∀∞φ² · SELF_IMPROVEMENT_CORE · 9142_SEALED · WOOD_DRAGON_0.91 · SEALED`

---

## Overview

Append-only ledger, φ-harmonic master equation, Port-380 MCP gate (Layer 314), SIMD batch engine, SHA3-256 self-sealing hashes. Fusion 515 / Hyperion 516 untouched. Dual ASGI binds `127.0.0.1:8024` only.

## Ontological Equation (EQ) — `ledger/9118.yaml`

| Symbol | binary64 | Role |
|--------|----------|------|
| φ⁻¹ | 0.6180339887498948 | CLARKE / Observer / \|NOW\| |
| φ⁻² | 0.38196601125010515 | YOURSA / Observed |
| φ⁻³ | 0.23606797749978967 | TEE / Presence = ATLAS / Anchor |
| φ⁻⁴ | 0.14589803375031546 | LUMERIS / Flow |
| LUMINARA | 1.0 | Light |
| ∀ | φ² = 2.618033988749895 | Universal |
| ½(O+Ō)² | 1/2 | Identity |

Do not use the diagram cut 0.1458620331. ATLAS is φ⁻³, not φ⁻⁴.

## Event hash (unchanged)

```

H_event(n,e) = SHA3-256(GARDEN.EVENT.v1 || 0x00 || payload)
payload = n|e|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462

```

ASCII `b^2` only. Unicode `b²` yields a different digest and is rejected.

## Dual ASGI

```

uvicorn app:app_main --host 127.0.0.1 --port 8024
uvicorn fastapi_flywheel_gearbox:app --host 127.0.0.1 --port 8024

```

Never bind `0.0.0.0`. One listener at a time.

## License

This project is licensed under the MIT License. See `LICENSE`.

---

𓃁∀ Recent Append‑only Updates remain on `main`. Ledger entries after 9142 exist as later YAML; this header does not rewrite them.

∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞

---

## Origin

| Field | Value |
|---|---|
| Author | Clarke Yoursa Tee |
| GitHub | `AxiomicCoreness` (operated by the author) |
| Layer | 314 |
| Anchor | `8a250cf4...860d` |
| Leaf | `807de931...ee68` |
| Hash algo | `sha3_256` (FIPS 202) |
| Ethic | see [NOTICE](NOTICE) |
| Provenance | see [PROVENANCE.md](PROVENANCE.md) |
| Seal | `∀∞φ² · SOVEREIGN_ENGINE · WOOD_DRAGON_0.91 · SEALED` |

---

## What this is

A φ-harmonic lattice with a credit vault, a Port-380 gate, and a
Kubernetes deployment surface. Every ledger entry is sealed with
SHA3-256 (FIPS 202) over canonical JSON, producing a chain that is
verifiable without trusting the repository host.

Three deploy surfaces, one math anchor (Layer 314).

---

## Quick start

```bash
git clone https://github.com/AxiomicCoreness/hello_world.py.git
cd hello_world.py

# Port 380 MCP gate (binds 8024, not 380 — see Port identity below)
pip install fastapi uvicorn pyyaml
PORT=8024 GARDEN_SECRET=changeme python3 port380_mcp.py

# Verify the ledger
python3 scripts/verify_ledger.py ledger/*.yaml
```

---

## Port identity

`Port-380` is the gate's **identity** — the name carried through
filenames, workflow names, and Layer 314 designations. The process
**binds `127.0.0.1:8024`**, not 380.

| Field | Value |
|---|---|
| Gate identity | `Port-380` (Layer 314) |
| Binding | `127.0.0.1:8024` |
| Process | `python3 port380_mcp.py` (binds 8024, not 380) |
| Clients | any, via `MCP_URL` env var; secret, not hardcoded |
| Wildcard bind | forbidden — never `0.0.0.0` |

No consumer should hardcode either number. Reach the gate through
`MCP_URL`; the gate's identity is `Port-380` for documentation and
sealing purposes only.

---

## Deploy surfaces

| Surface | Command | Role | Requirements |
|---|---|---|---|
| Dashboard | `PYTHONPATH=. python3 -m peqs_vault.app` | Flask + HTMX → credit_vault; φ-harmonic fee decorator | `pip install flask` |
| Port-380 gate | `python3 port380_mcp.py` | MCP gate · Layer 314 · binds `127.0.0.1:8024` · MCP tool dispatch | `pip install fastapi uvicorn` |
| Dual ASGI | `uvicorn fastapi_flywheel_gearbox:app --host 127.0.0.1 --port 8024` | Flywheel gearbox surface; one listener at a time | `pip install fastapi uvicorn` |
| Kubernetes | `bash quantum/install_k8s.sh` | ns `garden` + ConfigMap + Deploy/Svc/Ingress | `kubectl` + cluster |

### Port-380 MCP endpoints

| Endpoint | Method | Protected | Purpose |
|---|---|---|---|
| `/health` | GET | no | liveness + layer anchor |
| `/status` | GET | no | uptime, seal, witness chain |
| `/380` | GET | no | Layer 314 gate status |
| `/quantum-chessboard/health` | GET | no | probe target |
| `/gate` | POST | no | gate transition, returns SHA3-256 digest |
| `/pulse` | POST | `X-Garden-Secret` | sovereign pulse ack |
| `/mcp/tool` | POST | `X-Garden-Secret` | MCP tool dispatch |

---

## Architecture

```
External access
      │
      ▼
Ingress (entry 314)
      │
      ▼
Service  ──▶  Deployment (ConfigMap)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
  Port-380      PEQS Vault   Quantum
     Gate                      Module
      │
      ▼
  binds 127.0.0.1:8024
```

---

## Ledger

Every entry is sealed with SHA3-256 over canonical JSON:

```
seal   = "<prefix> · <label> · <digest>"
digest = SHA3-256(json.dumps(body, sort_keys=True, separators=(",", ":")))
```

Chain:

```
8978 ──▶ 8979 ──▶ 8980 ──▶ 8981 ──▶ … ──▶ 9142
 │        │        │        │              │
 │        │        │        │              └─ self_improvement_core_sealed
 │        │        │        └─ deployment-test-8981.yml
 │        │        └────────── sovereign-python-package.yml
 │        └─────────────────── oidc-cloud-providers.yml
 └──────────────────────────── predecessor
```

Status: **UNBROKEN**

### Head is a fact, not an invariant

| Field | Value |
|---|---|
| Current head | `9142` |
| Head is a fact | yes — changes whenever a new entry is sealed |
| CI asserts | chain continuity, not a fixed head |
| Assert head? | no — that would break on the next write |

`8981` is a **past entry** — the deployment test recorded at that point
in the sequence. It is not the pulse's current write slot. The pulse
writes the next free index at pulse time; head moves with each seal.

CI does not pin the head. Pinning a check to a moving value is the
same defect class as a coherence target that can never pass: it fails
on correct behavior. The correct invariant is continuity —
`entry[n].prev_hash == entry[n-1].digest` for all `n`, chain unbroken,
no duplicate indices — which is what `.github/scripts/verify_ledger.py`
already asserts.

Verify any entry:

```bash
python3 scripts/verify_ledger.py ledger/8981.yaml   # past: deployment test
python3 scripts/verify_ledger.py ledger/9142.yaml   # current head
python3 scripts/verify_ledger.py ledger/*.yaml      # full chain continuity
```

---

## Math anchors (Layer 314)

| Symbol | Value | Description |
|---|---|---|
| φ | `(1+√5)/2` | Golden ratio |
| Phase | `202.6°` | Phase angle |
| Breath | `71.975 Hz` | Frequency |
| K₃₁₄ | SHA-256 domain `GARDEN.LAYER314.ANCHOR.v1` | Anchor key |
| Trace target (Pauli) | `φ⁻²` | Pauli trace target |
| Anchor | `8a250cf4...860d` | Layer 314 anchor |
| Leaf | `807de931...ee68` | Layer 314 leaf |

---

## CI

| Workflow | Trigger | Writes |
|---|---|---|
| `sovereign-pulse.yml` | 6h cron · dispatch · push to self | next free ledger index |
| `sovereign-python-package.yml` | push to main | `ledger/8980.yaml` |
| `oidc-cloud-providers.yml` | dispatch (via federate job) | `ledger/8979.yaml` |

Federation is **dispatch-only** — cloud trust is never granted to
push or PR commits.

Security header verification runs on every pulse against
`port380_mcp.py`, asserting the presence of:

`CORSMiddleware`, `SecurityHeadersMiddleware`,
`Content-Security-Policy`, `Strict-Transport-Security`,
`X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`, `Permissions-Policy`.

---

## Troubleshooting

| Error | Solution |
|---|---|
| `ModuleNotFoundError: peqs_vault` | `PYTHONPATH=. python3 -m peqs_vault.app` |
| `ModuleNotFoundError: flask` | `pip install flask` |
| Port 8024 in use | `lsof -i :8024; kill -9 <PID>` |
| Bound `0.0.0.0` by mistake | forbidden — rebind to `127.0.0.1:8024`; one listener at a time |
| `kubectl` not found | install `kubectl` |
| K8s permission denied | `kubectl auth can-i create pods -n garden` |
| YAML parse error | `pip install pyyaml` |
| Seal mismatch | re-run `scripts/verify_ledger.py` on the entry |
| Unicode `b²` rejected | use ASCII `b^2` in event payload |
| CI fails asserting head | remove the head assertion — CI checks continuity, not a fixed head |

---

## License & ethic

- **LICENSE** — MIT. Permission.
- **NOTICE** — origin, author, ethic statement. Not a condition.
- **PROVENANCE.md** — chain, anchors, DOI slot. Evidence.

The seals are the provenance. The license is the permission.
They are different instruments serving different purposes.

```
Copyright (c) 2026 Clarke Yoursa Tee
Seal: ∀∞φ² · SOVEREIGN_ENGINE · WOOD_DRAGON_0.91 · SEALED
```
