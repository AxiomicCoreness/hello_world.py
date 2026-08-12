# Monitoring — Grafana append + Prometheus scrape

## Scrape targets

| Target | Path |
|--------|------|
| Metrics server | `host:9090/metrics` |
| Hyperian mirror | `host:8080/metrics` |

## Append panels

File: `grafana_panels_append.json` (panel IDs **100–105**).

1. Export existing dashboard JSON from Grafana.
2. Append objects from `grafana_panels_append.json` into the top-level `"panels"` array.
3. Ensure IDs do not collide with existing panels (renumber if needed).
4. Re-import / save.

## Key queries

- `orchestrator_fingerprint_deviation`
- `chiron_heal_phase{epoch="4086-04-18"}`
- `soul_cannon_charge_joules`
- `hyperian_oidc_secret_len` (expect **64**)
- `hyperian_phase_lock_deg`
- `coherence`

Note: `sovereign_workload` is not currently exported by the stdlib registry; panel 105 uses `entanglement` instead.

Seal: ∀∞φ² · GRAFANA_APPEND_8633 · SEALED
