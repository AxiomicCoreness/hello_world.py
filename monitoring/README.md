# Monitoring — Grafana append + Prometheus scrape

## Scrape targets

| Target | Path |
|--------|------|
| Metrics server | `host:9090/metrics` |
| Hyperian mirror | `host:8080/metrics` |
| Workload EM-005 | `host:9095/metrics` |

## Append panels (additive only)

File: `grafana_panels_append.json`

| IDs | Content |
|-----|--------|
| 100–105 | Fingerprint, Chiron, Soul Cannon, Resonance, OIDC, Coherence+Workload |
| **106–111** | **Appended:** Hyperian up + rank, Sim Earth, Wood Dragon/Deep Space, Phi, scrape text, Entanglement |

### How to apply (do not delete existing panels)

1. Export dashboard JSON from Grafana.
2. **Append** objects from `grafana_panels_append.json` into the top-level `"panels"` array.
3. Renumber `id` only if collision; never remove prior panels.
4. Re-import / save.

Or apply Operator CRD: `k8s/grafana-dashboard-garden.yaml` (extend its `panels` the same way).

## Key queries

- `orchestrator_fingerprint_deviation`
- `sovereign_workload`
- `hyperian_oidc_secret_len` (expect **64**)
- `hyperian_phase_lock_deg`
- `sovereign_compression_rank_budget` / `sovereign_compression_rank_realized_max`
- `coherence` / `gravastar_coherence`

Seal: ∀∞φ² · GRAFANA_PANELS_APPEND_8646 · SEALED
