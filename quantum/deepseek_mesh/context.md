# DeepSeek Mesh Quadrant Context

Entry: 8844/8845 (+ key setup 8831)
Seal: ∀∞φ² · DEEPSEEK_MESH · WOOD_DRAGON_0.91 · SEALED
Witness: 8843 → 8844 → 8845 → … → 8831 — UNBROKEN

## Invariants
- Garden: coherence=1.0, phase=202.6°, entropy=φ⁻¹⁴¹⁸
- External model surface: **DeepSeek only** (offline | deepseek | dsh)
- MCP gate: `/health` `/pulse` `/gate` `/metrics` …

## Components
- `client.py` — thin chat/status/echo over adapter
- `dsh_adapter.py` — DeepSeek-only complete/probe
- `endpoint.py` — FastAPI MCP surface
- `dsh_adapter` modes: offline, deepseek, dsh

## Environment Variables
| Name | Role |
|------|------|
| `DEEPSEEK_API_KEY` | Bearer for online DeepSeek |
| `DEEPSEEK_BASE_URL` | default `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` / `DSH_MODEL` | model id |
| `GARDEN_SECRET` | `/pulse` header auth |
| `PORT` | listen port |

See **docs/deepseek-api-key-setup.md** and **.env.example**.

## Append-Only Rule
All additions to this quadrant must be append-only where possible.
