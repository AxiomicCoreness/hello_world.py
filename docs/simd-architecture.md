# SIMD Batch Architecture — Benefits

**Image:** `axiomic/sovereign-engine:latest`  
**Base:** `ccc59bf7` (SIMD) · Dockerfile `2c4f4f22` · Ledger `8793`

## What runs in one atomic cycle

| Phase | Surface | Role |
|-------|---------|------|
| 0 | `/step` (local) | Coherence drift + phase lock toward 202.6° |
| 1 | `/mesh` (local) | φ-coupled node map (E9 / choir sketch) |
| 2 | `dispatch_cycle` | A/B/C plan; DeepSeek optional |
| 3 | MCP `/pulse` | HTTP branch seal (optional) |
| 4 | `/deepseek/stream` | LLM stream collect (optional) |

Then **one** leaky-integral PID update on `e_batch = mean(errors)`.

## Benefits vs sequential curls

1. **Latency** — `asyncio.gather` overlaps independent work; wall time ≈ max(phase) not sum(phase).
2. **Atomicity** — single result dict + seal (`SIMD_BATCH_STEP_OK` / `_PARTIAL`); no partial ledger without PID.
3. **Control coherence** — PID sees aggregated error once per cycle (matches batch methodology 0053).
4. **Determinism** — same inputs → same local step/mesh; HTTP phases optional behind `--no-http`.
5. **Cluster fit** — CronJob `0 */6` runs offline SIMD without needing live Ingress; Deployment serves `/mesh` + `/deepseek/*` continuously.
6. **Fiber-safe DeepSeek** — client lifecycle (PENDING→ACTIVE/FAILED) prevents idle dead-ends inside parallel tasks.

## Operators

```bash
# Local
bash scripts/deploy_simd.sh
bash scripts/deploy_simd.sh --http

# Cluster reset after image push
bash scripts/cluster_reset.sh
bash scripts/cluster_reset.sh --with-http-check

# Apply CronJob only
kubectl apply -f kubernetes/cronjob-simd-step.yaml -n sovereign-garden
```

## HTTP surfaces (when Deployment is up)

```bash
curl -s -X POST http://localhost:8000/mesh -H 'Content-Type: application/json' -d '{"nodes":7}'
curl -s http://localhost:8000/deepseek/status
curl -s -X POST http://localhost:8000/deepseek/complete -H 'Content-Type: application/json' \
  -d '{"prompt":"mesh retune","max_tokens":64}'
```
