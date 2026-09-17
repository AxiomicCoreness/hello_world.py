# Public search — AxiomicCoreness/hello_world.py

**License:** MIT (`LICENSE` at repo root). GitHub classifies this repo as MIT.

**Canonical URL:** https://github.com/AxiomicCoreness/hello_world.py

**Description (About):** sovereign_engine_V5  
Suggested longer About text (set in UI if desired):
`Sovereign Engine V5 — φ-harmonic reward protocol, MCP/FastAPI surfaces, append-only ledger`

---

## Queries that should resolve

```
AxiomicCoreness hello_world.py
repo:AxiomicCoreness/hello_world.py
license:MIT AxiomicCoreness
AxiomicCoreness sovereign_engine_V5 MIT
```

GitHub code search (signed in):

```
repo:AxiomicCoreness/hello_world.py license MIT
repo:AxiomicCoreness/hello_world.py FILLED False 8024
repo:AxiomicCoreness/hello_world.py reward_protocol
repo:AxiomicCoreness/hello_world.py fiduciary_node_rewards
```

Web search engines lag. Direct URL and GitHub `license:MIT` / code search work now.

---

## Topics (About → Topics)

Add in the GitHub UI if not already set:

`python` · `mit-license` · `fastapi` · `pydantic` · `sovereign-engine` · `axiomiccoreness`

CLI (owner):

```bash
gh repo edit AxiomicCoreness/hello_world.py \
  --add-topic python \
  --add-topic mit-license \
  --add-topic fastapi \
  --add-topic pydantic \
  --add-topic sovereign-engine \
  --add-topic axiomiccoreness
```

---

## Key files (discovery anchors)

| Path | Role |
|------|------|
| `reward_protocol.py` | SPU aggregation, Gate, sidecar verdict |
| `fiduciary_node_rewards.py` | Tier-based rewards; pool ≈ 8701.5233078 |
| `tests/test_reward_protocol.py` | Protocol + fiduciary tests |
| `.github/workflows/reward-distribution.yml` | Reward CI |
| `ledger/517.yaml` | Ideal W / tier design note |
| `ledger/518.yaml` | Pool verification record |
| `docs/spu_reward_loops.md` | Mermaid loops + sidecar contract |
| `scripts/spu_reward.py` | Minimal SPU reference |
| `mcp/port380_mcp.py` | MCP gate (`/healthz`) |
| `POLICY.md` | Constitutional policy |

---

## Invariants (search-friendly constants)

- Bind: ASGI North Star `127.0.0.1:8024` (not `0.0.0.0` for user-facing ASGI)
- MCP: scoped bind via `MCP_BIND_HOST` (default mesh-facing where policy allows)
- License: MIT
- Public: yes
