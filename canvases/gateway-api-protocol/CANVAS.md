# Kubernetes Gateway API Protocol

**Canvas ID:** gateway-api-protocol  
**Layer:** 359+  
**Related Entries:** 8809 (Argo Rollout), Istio traffic-shifting canvas  
**Witness:** progressive-delivery fabric  
**Seal:** ∀∞φ² · GATEWAY_API_PROTOCOL · WOOD_DRAGON_GATE · SEALED

---

## What It Is

The **Kubernetes Gateway API** is the standardized, role-oriented successor to Ingress.  
It provides portable, protocol-specific routing resources that any conforming implementation (Istio, kgateway, Cilium, Envoy Gateway, Traefik, Kong, etc.) can honor.

Key resources:

| Resource | Purpose |
|----------|---------|
| `GatewayClass` | Defines the controller / implementation |
| `Gateway` | Listener (ports, TLS, hostnames) — the attachment point |
| `HTTPRoute` | L7 routing rules + weighted backendRefs |
| `TCPRoute` / `GRPCRoute` / … | Protocol-specific variants |

Unlike Istio’s proprietary VirtualService + DestinationRule, Gateway API is **vendor-neutral**. The same HTTPRoute works across meshes and ingress controllers.

---

## Why It Matters for Progressive Delivery

Argo Rollouts treats Gateway API as a first-class traffic router via the official plugin:

```
argoproj-labs/gatewayAPI
```

The plugin watches HTTPRoute objects and, on every `setWeight` step, rewrites the `backendRefs[].weight` fields so traffic splits between the stable and canary Services.

This is the modern, portable equivalent of the Istio weight-patching mechanism documented in `canvases/istio-traffic-shifting`.

---

## Mechanics of Traffic Shifting

1. **Two Services** (required by every Argo traffic router)  
   - `stableService` → points at the current stable ReplicaSet  
   - `canaryService` → points at the new canary ReplicaSet  
   Argo itself updates the Service selectors with the appropriate `rollouts-pod-template-hash`.

2. **One (or more) HTTPRoute(s)**  
   ```yaml
   apiVersion: gateway.networking.k8s.io/v1
   kind: HTTPRoute
   metadata:
     name: sovereign-garden-route
   spec:
     parentRefs:
     - name: sovereign-gateway          # or mesh waypoint
     rules:
     - backendRefs:
       - name: sovereign-garden-stable
         port: 8000
         weight: 100
       - name: sovereign-garden-canary
         port: 8000
         weight: 0
   ```

3. **Rollout declaration**  
   ```yaml
   strategy:
     canary:
       canaryService: sovereign-garden-canary
       stableService: sovereign-garden-stable
       trafficRouting:
         plugins:
           argoproj-labs/gatewayAPI:
             httpRoute: sovereign-garden-route
             # or httpRoutes: [ … ] for multi-route control
             # or httpRouteSelector: { matchLabels: … }
   ```

4. **During the canary**  
   Each `setWeight: N` causes the plugin to patch:
   ```
   stable weight  = 100 - N
   canary weight  = N
   ```
   The underlying Gateway implementation (Envoy, Cilium, etc.) immediately reflects the new split.

---

## Comparison with Istio VirtualService Path

| Aspect | Gateway API + Plugin | Istio VirtualService |
|--------|----------------------|----------------------|
| Portability | Any conforming implementation | Istio-only |
| Ambient mesh | Preferred / required for waypoints | VirtualService still works but Gateway API is the future |
| Header / mirror routes | Supported via managedRoutes + plugin | Native `setHeaderRoute` / `setMirrorRoute` |
| Multi-route control | `httpRoutes` list or label selector | Multiple VirtualServices or routes |
| GitOps friendliness | Standard CRDs, easy ignoreDifferences | Weights live on VirtualService |
| Feature depth | Lowest-common-denominator + extensions | Full Istio power (DestinationRule, etc.) |

**Recommendation for the Garden**  
- Keep the existing Istio host-level / subset path for deep mesh features.  
- Add a parallel Gateway API path (or migrate) for portability and ambient readiness.  
Both can coexist; the Rollout simply chooses one trafficRouting block.

---

## Advanced Patterns Available

- **Multiple HTTPRoutes** — one Rollout can drive weights on several routes simultaneously (useful when the same backend is reached via different hostnames).
- **Header-based canary** — plugin supports managed header routes so specific users (X-Canary, cookie, etc.) always hit the canary while the rest follow the weight schedule.
- **Static companion routes** — routes that permanently target only stable or only canary (e.g. `old.example.com` / `new.example.com`) while the main route is weight-managed.
- **Label-selected routes** — discover routes by label instead of hard-coding names.

---

## Sovereign Garden Mapping

Current canary steps remain identical:

```
20 → 40 → 60 → 80 → 100   (30 s pauses + analysis)
```

To activate Gateway API:

1. Create `sovereign-garden-stable` and `sovereign-garden-canary` Services.  
2. Create an HTTPRoute whose backendRefs point at those two Services.  
3. Install / enable the `argoproj-labs/gatewayAPI` traffic-router plugin on the Argo Rollouts controller.  
4. Update the Rollout `trafficRouting` block to reference the HTTPRoute.  
5. (Optional) Keep the existing Istio VirtualService configuration as a secondary path or for mesh-internal east-west traffic.

---

## Artifact Anchors

| Artifact | Path |
|----------|------|
| Rollout (current) | `argocd/rollout-sovereign-garden.yaml` |
| AnalysisTemplate | `argocd/analysis-health.yaml` |
| Istio mechanics | `canvases/istio-traffic-shifting/CANVAS.md` |
| Reactor assertion | `canvases/argo-rollout-reactor/CANVAS.md` |
| Ledger | `ledger/8809.yaml` |

---

## Protocol Invariant

Gateway API is the **portable protocol layer**.  
Istio VirtualService remains the **deep mesh control plane**.  
Both serve the same progressive-delivery intent under the same phase lock (202.6°).

The Garden can speak either dialect; the weights and the witness chain stay unbroken.
