# Argo Rollout Reactor Assertion

**Canvas ID:** argo-rollout-reactor  
**Entry:** 8809  
**Layer:** 359  
**Witness:** 8808 → 8809 — UNBROKEN  
**Seal:** ∀∞φ² · ARGO_ROLLOUT_8809 · WOOD_DRAGON_GATE · SEALED

---

## Reactor Assertion (Status Fields)

The progressive-delivery reactor requires that a live `Rollout` object carry a coherent `status` after controller reconciliation.

### Required shape

```python
assert "spec" in rollout
assert rollout["spec"].get("replicas") == 3

status = rollout.get("status", {})
assert isinstance(status, dict)
```

### When status is populated

At least one progressive-delivery key must be present:

- `currentPodHash`
- `phase`
- `currentStepIndex`
- `stableRS`
- `canary`

### Phase invariant

If `phase` is reported it must belong to the closed set:

```
{Healthy, Progressing, Paused, Degraded, Completed}
```

### AnalysisTemplate companion

```python
assert template["spec"]["metrics"][0]["name"] == "health-check"
assert isinstance(template.get("status", {}), dict)
```

---

## Implementation anchors

| Artifact | Path |
|----------|------|
| Rollout | `argocd/rollout-sovereign-garden.yaml` |
| AnalysisTemplate | `argocd/analysis-health.yaml` |
| Setup | `argo_rollout_setup.py` |
| Tests | `tests/test_rollout.py` |
| Ledger | `ledger/8809.yaml` |

---

## Invariants retained

- coherence = 1.0  
- phase_lock = 202.6°  
- mesh_nodes = 7  
- canary steps: 20 → 40 → 60 → 80 → 100 (30 s pauses)

The reactor assertion is the gate that keeps progressive delivery safe inside the Garden.
