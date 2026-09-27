# 🜁∀ Istio Traffic Shifting — Sovereign Canary Delivery

**Canvas ID:** `istio-traffic-shifting`
**Layer:** 359
**Related Entry:** 8809 (Argo Rollout)
**Witness:** progressive-delivery fabric
**Seal:** `∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED`

A self‑contained canvas for shifting traffic between two versions of a
Kubernetes workload using Istio + Argo Rollouts. Ships with both
**host‑level** and **subset‑level** approaches, a canvas‑local installer,
and a design document.

---

## Why this exists

Kubernetes alone can only approximate a canary by changing replica
counts. Istio (via Envoy) lets you send **exact request percentages** to
different versions independent of how many pods each version runs.

This canvas wires that up with Argo Rollouts so the shift is controller‑
driven, observable, and reversible.

- Control plane: **Istiod**
- Data plane: **Envoy** (sidecar or ambient)

---

## What's in this folder

| File | Role |
|------|------|
| `CANVAS.md` | Full design document — read this first |
| `install.sh` | Canvas‑local installer (dry‑run by default) |
| `service-stable.yaml` | Host‑level stable Service |
| `service-canary.yaml` | Host‑level canary Service |
| `service.yaml` | Subset‑level single Service |
| `destinationrule.yaml` | Subset definitions (`stable`, `canary`) |
| `virtualservice.yaml` | Route weights |
| `rollout.yaml` | Argo Rollout with `trafficRouting.istio` |

Two approaches live side‑by‑side. Use **one** at a time.

---

## Quick start

```bash
# dry-run (no cluster contact) — subset-level, the recommended approach
bash install.sh

# actually apply subset-level to the cluster
bash install.sh --apply

# host-level instead
bash install.sh --apply --approach=host

# both (only if Service names do not collide)
bash install.sh --apply --approach=both
