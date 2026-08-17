# Istio Traffic Shifting Mechanics

**Canvas ID:** istio-traffic-shifting  
**Layer:** 359+  
**Related Entry:** 8809 (Argo Rollout)  
**Witness:** progressive-delivery fabric  
**Seal:** ∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED

---

## Core Principle

Istio **decouples traffic routing from pod scaling**.

Kubernetes alone can only approximate canaries by changing replica counts.  
Istio (via Envoy) lets you send exact request percentages to different versions independent of how many pods each version runs.

Control plane: Istiod  
Data plane: Envoy (sidecar or ambient)

---

## Two Approaches with Argo Rollouts

| Approach | Mechanism | Required Objects | Controller Action |
|----------|-----------|------------------|-------------------|
| **Host-level** | Two Kubernetes Services | Rollout + canaryService + stableService + VirtualService | Updates Service selectors (`rollouts-pod-template-hash`) **and** VirtualService weights |
| **Subset-level** (preferred) | One Service + DestinationRule subsets | Rollout + Service + VirtualService + DestinationRule | Injects `rollouts-pod-template-hash` into subset labels **and** adjusts VirtualService weights |

Current sovereign-garden Rollout references route names `canary` / `stable` (host-level style).

---

## Weight Shift Sequence

1. **Initial**  
   VirtualService: stable = 100, canary = 0  
   (Istio requires weights sum exactly to 100.)

2. **Argo `setWeight: N`**  
   Controller patches:
   ```yaml
   route:
   - destination: { host: stable-svc  (or subset: stable)  }
     weight: 100 - N
   - destination: { host: canary-svc  (or subset: canary)  }
     weight: N
   ```

3. **Envoy reload**  
   Istiod pushes config → Envoy updates route weights (near-instant for HTTP).

4. **Analysis / pause**  
   Traffic holds at the new ratio while AnalysisTemplate runs or pause duration elapses.

5. **Promotion**  
   Final `setWeight: 100` → canary becomes new stable; old stable ReplicaSet scales down.

---

## Constraints & Edge Cases

- Weights **must sum to 100** — Istio rejects or ignores invalid splits.
- Stable ReplicaSet stays fully scaled during the rollout (instant rollback capability).
- Header-based (`setHeaderRoute`) and mirror (`setMirrorRoute`) routes can be layered on top.
- Known edge case: mid-rollout `setCanaryScale` can momentarily force traffic back to 100 % stable. Prefer `setCanaryScale: matchTrafficWeight: true` or carefully order scaling vs weight steps.
- GitOps: Argo CD should `ignoreDifferences` on VirtualService weights so the Rollout controller remains the live source of truth.

---

## Sovereign Garden Mapping (Entry 8809)

Current canary steps:

```
20 → 40 → 60 → 80 → 100   (30 s pauses)
```

These map 1:1 onto successive VirtualService weight patches.

### Missing for precise Istio shifting

- Explicit `canaryService` / `stableService` **or** DestinationRule subsets
- Concrete VirtualService named `sovereign-garden-vs` with matching route names
- Optional DestinationRule if choosing subset-level

Without the above, the Rollout still advances ReplicaSets but falls back to replica-count approximation instead of precise Istio weights.

---

## Recommended Next Weave

1. Choose host-level vs subset-level.
2. Materialise Service(s) + VirtualService (+ DestinationRule).
3. Wire them into `trafficRouting.istio` on the Rollout.
4. Optionally enrich AnalysisTemplate with success-rate / latency metrics from Istio telemetry.

---

## Artifact Anchors

| Artifact | Path |
|----------|------|
| Rollout | `argocd/rollout-sovereign-garden.yaml` |
| AnalysisTemplate | `argocd/analysis-health.yaml` |
| Reactor assertion | `canvases/argo-rollout-reactor/CANVAS.md` |
| Ledger | `ledger/8809.yaml` |

The Garden delivers progressively when traffic weights and ReplicaSets move in lock-step under the same phase lock (202.6°).
