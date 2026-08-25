# 🜁∀ Istio Traffic Shifting — Sovereign Canary Delivery

**Canvas ID:** istio-traffic-shifting  
**Layer:** 359+  
**Related Entry:** 8809 (Argo Rollout)  
**Witness:** progressive-delivery fabric  
**Seal:** `∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED`

---

## 🔷 Core Principle

Istio **decouples traffic routing from pod scaling**.

Kubernetes alone can only approximate canaries by changing replica counts.  
Istio (via Envoy) lets you send exact request percentages to different versions independent of how many pods each version runs.

**Control plane:** Istiod  
**Data plane:** Envoy (sidecar or ambient)

---

## 🔷 Two Approaches with Argo Rollouts

| Approach | Mechanism | Required Objects | Controller Action |
|----------|-----------|------------------|-------------------|
| **Host-level** | Two Kubernetes Services | Rollout + canaryService + stableService + VirtualService | Updates Service selectors (`rollouts-pod-template-hash`) **and** VirtualService weights |
| **Subset-level** (preferred) | One Service + DestinationRule subsets | Rollout + Service + VirtualService + DestinationRule | Injects `rollouts-pod-template-hash` into subset labels **and** adjusts VirtualService weights |

Current `sovereign-garden` Rollout references route names `canary` / `stable` (host-level style).

---

## 🔷 Weight Shift Sequence

1. **Initial**  
   VirtualService: stable = 100, canary = 0  
   (Istio requires weights sum exactly to 100.)

2. **Argo `setWeight: N`**  
   Controller patches:
   ```yaml
   route:
   - destination: { host: stable-svc  (or subset: stable) }
     weight: 100 - N
   - destination: { host: canary-svc  (or subset: canary) }
     weight: N
