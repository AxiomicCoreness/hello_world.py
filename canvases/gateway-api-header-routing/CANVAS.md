# Canvas — Gateway API Header Routing (Sovereign Garden)

**Entry:** 8812 (single pin) · 8813 (multi-stage)  
**Seal lineage:** `WOOD_DRAGON_GATE · 0.91`  
**Traffic router:** `argoproj-labs/gatewayAPI` plugin  
**Companion:** Entry 8811 Services + HTTPRoute

## Intent

Pin selected clients to the canary via HTTP headers while the rest of traffic follows the proportional weight schedule. Header rules are **independent** of `setWeight`.

## Surfaces

| Artifact | Role |
|----------|------|
| `argocd/rollout-sovereign-garden-gateway-header.yaml` | Single pin: `X-Canary: true` |
| `argocd/rollout-sovereign-garden-gateway-multistage.yaml` | Staged pins: `X-Canary-Stage: early\|mid` |
| `argocd/argocd-ignore-differences-httproute.yaml` | Argo CD does not overwrite live weights during canary |
| `argocd/sovereign-garden-{stable,canary,httproute}.yaml` | Backend Services + initial 100/0 HTTPRoute |

## Weight schedule (background)

```
20 → 80/20
40 → 60/40
60 → 40/60
80 → 20/80
100 → 0/100
```

(Multi-stage variant uses 10 → 40 → 80 → 100.)

## Header contract

| Header | Match | Effect |
|--------|-------|--------|
| `X-Canary` | exact `true` | 100% canary (8812) |
| `X-Canary-Stage` | exact `early` | 100% canary while early-qa active (8813) |
| `X-Canary-Stage` | exact `mid` | 100% canary while mid-qa active (8813) |

Cleanup: empty `setHeaderRoute` (name only) removes the injected rule before the Rollout finishes.

## Prerequisites

1. Argo Rollouts controller with plugin `argoproj-labs/gatewayAPI` (v0.13.0+).
2. Gateway API ≥ 1.2 (named rules preferred).
3. Provider that supports header matches on HTTPRoute (Istio ambient, kgateway, Cilium, Traefik, …).
4. RBAC: Rollouts SA can patch HTTPRoute.

## Clock

`wood_dragon_gate_0.91` = τ_FRB = 78624 s (mint / Choir heartbeat). Not a traffic weight — the deployment plane seal suffix.

## Status

Source-only manifests. Not executed from the authoring environment.
