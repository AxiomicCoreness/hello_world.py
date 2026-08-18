# Canvas — Gateway API Header Routing (Sovereign Garden)

**Entry:** 8812 (single pin) · 8813 (multistage intro) · **8814 (weights refined)**  
**Seal lineage:** `WOOD_DRAGON_GATE · 0.91`  
**Traffic router:** `argoproj-labs/gatewayAPI` plugin  
**Companion:** Entry 8811 Services + HTTPRoute

## Intent

Pin selected clients to the canary via HTTP headers while the rest of traffic follows the proportional weight schedule. Header rules are **independent** of `setWeight`.

## Surfaces

| Artifact | Role |
|----------|------|
| `argocd/rollout-sovereign-garden-gateway-header.yaml` | Single pin: `X-Canary: true` (8812) |
| `argocd/rollout-sovereign-garden-gateway-multistage.yaml` | Staged pins + **20→40→60→80→100** (8814) |
| `argocd/argocd-ignore-differences-httproute.yaml` | Argo CD ignores live weights during canary |
| `argocd/sovereign-garden-{stable,canary,httproute}.yaml` | Backend Services + initial 100/0 HTTPRoute |

## Refined weight schedule (background, Entry 8814)

| Stage | setWeight | stable / canary | Header pins |
|-------|-----------|-----------------|-------------|
| 0 | 20 | 80 / 20 | `early` |
| 1 | 40 | 60 / 40 | `early` + `mid` |
| 2 | 60 | 40 / 60 | `mid` (early cleared) |
| 3 | 80 | 20 / 80 | `mid` |
| 4 | 100 | 0 / 100 | — (mid cleared) |

Aligned with Entry 8811 proportional model. Pause duration: 30s between stages.

## Header contract

| Header | Match | Window |
|--------|-------|--------|
| `X-Canary` | exact `true` | full canary pin (8812 single-route variant) |
| `X-Canary-Stage` | exact `early` | stages 0–1 |
| `X-Canary-Stage` | exact `mid` | stages 1–3 |

Cleanup: empty `setHeaderRoute` (name only) removes the injected rule.

## Prerequisites

1. Argo Rollouts controller with plugin `argoproj-labs/gatewayAPI` (v0.13.0+).
2. Gateway API ≥ 1.2 (named rules preferred).
3. Provider that supports header matches on HTTPRoute.
4. RBAC: Rollouts SA can patch HTTPRoute.

## Clock

`wood_dragon_gate_0.91` = τ_FRB = 78624 s (mint / Choir heartbeat).

## Status

Source-only manifests. Not executed from the authoring environment.
