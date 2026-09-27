# codespace-phi-draft

Signitorial: Clarke Yoursa Tee

Option B landing. Isolated from sealed `k8s/codespace/` (9157) and from
live `celestial/saturn_soul_cannon.py` / `celestial/trappist_choir.py`.

| Live (main) | This draft |
| --- | --- |
| `k8s/codespace/` namespace `garden-codespace` | `garden-codespace-phi-draft` |
| MCP `FILLED=false` | MCP slot empty (no 380, no Ingress) |
| Dual ASGI `127.0.0.1:8024` | same |
| `PHI_MINUS_1000` not in env | `1.028868213399699e-209` (φ⁻¹⁰⁰⁰) |
| quota 4/8/8/16 Gi | floor(φⁿ) 2/6/11/17 |

Apply only after operator review, against a scratch cluster:

```
kubectl apply -f k8s/codespace-phi-draft/
```

D33: `python:3.12-slim` does not contain `celestial/`. Image is a
placeholder. Import will fail until a custom image exists.
