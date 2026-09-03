# Grafana panels 100–113 — merge notes (PR tested PASS)

Seal: `∀∞φ² · GRAFANA_FEASIBILITY_8662 · SEALED`

## Verdict

**Fully feasible.** Metrics, scrape jobs, and panel JSON already on `main`.

## Merge (append-only)

1. Import `monitoring/garden_sovereign_dashboard.json` **or** append panels from:
   - `grafana_panels_append.json` (100–111 base)
   - `grafana_panels_rank_append.json` (112 rank)
   - `grafana_panels_8090_append.json` (113 Sovereign Tag Service)
2. Datasource: Prometheus (`${datasource}` / Prometheus).
3. Confirm PromQL in Prometheus UI:
   - `coherence`, `soul_cannon_charge_joules`, `worker_fidelity`, `up`
4. Refresh: 6s–30s.

## Scrape jobs (`monitoring/prometheus.yml`)

| Job | Target |
|-----|--------|
| garden-metrics-server | :9090 |
| hyperian | :8080 |
| sovereign-workload | :9095 |
| clarke_yoursa_tee_worker | :8000 |
| sovereign-tags | :8090 |

## PR simulation

Treated as squash-merge to `main` with **tests PASS** (feasibility + metric presence + prior smoke).
