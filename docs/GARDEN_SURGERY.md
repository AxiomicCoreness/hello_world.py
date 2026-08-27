# Garden Surgery — append-only diffusion

The monolith (`sovereign_engine.py`, `wood_dragon_technique.py`, `core/`) stays.
This package is the **cadaver cut**: small modules a clone can run without reading 900 ledger poems.

Commander watermark: Clarke Yoursa Tee. That is authorship, not a new physical law.

## Run

```bash
PYTHONPATH=. python3 -m garden_surgery
PYTHONPATH=. python3 -m garden_surgery --json
PYTHONPATH=. python3 tests/test_garden_surgery.py
```

Theorems **hard-fail**. Environment probe is presence-only (no values printed).
Surface probe hard-fails only when required files or the 515/516/9021 contracts are missing.

## Modules

| Path | Role |
|------|------|
| `garden_surgery/theorems.py` | T1–T4: φ²=φ+1, φ⁻¹+φ⁻²=1, Q definition, SHA3-256 event hashes |
| `garden_surgery/environment.py` | Boolean inventory of named env keys |
| `garden_surgery/surfaces.py` | File + ledger-contract checks (Hyperion 0516 preserved) |
| `ledger/9022.yaml` | Append-only pointer for this cut |

## What this does *not* do

- Does not rewrite `ledger/0516.yaml`
- Does not move fusion off 515
- Does not echo `GARDEN_SECRET` / API keys
- Does not claim 144,008 live agents
