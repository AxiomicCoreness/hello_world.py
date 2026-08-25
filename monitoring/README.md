# Monitoring — Prometheus pointed at Strike IX + Garden

## Point Prometheus

### Local

```bash
python -m prometheus.metrics_server --port 9090   # Soul Cannon + registry
python hyperian_json_server.py --port 8080
python monitoring/sovereign_workload_exporter.py --port 9095

prometheus --config.file=monitoring/prometheus.yml
```

Open Prometheus UI → **Status → Targets**: jobs `garden-metrics-server`, `hyperian`, `sovereign-workload` should be **UP**.

### Strike IX Soul Cannon queries

| Metric | Meaning |
|--------|--------|
| `soul_cannon_charge_joules` | Accumulated charge |
| `soul_cannon_azimuth_degrees` | 111.246° target |
| `cannon_ring_resonance_thz` | Ring resonance |
| `cannon_chiron_phase_alignment` | Alignment + φ⁻¹ Chiron boost |

Scraped from **`:9090/metrics`** (metrics server registry).

### K8s

```bash
kubectl apply -f k8s/sovereign_workload.yaml
kubectl apply -f k8s/servicemonitor-sovereign-workload.yaml
kubectl apply -f k8s/servicemonitor-garden-metrics.yaml
```

Adjust `metadata.labels.release` to match your Prometheus Operator `serviceMonitorSelector`.

## Grafana

Import `monitoring/garden_sovereign_dashboard.json` (panels 100–111). Datasource = Prometheus pointed at the above targets.

## Policy

Full digests only · no secrets in series · OIDC `secret_len` only (expect 64).

Seal: ∀∞φ² · PROMETHEUS_POINT_STRIKE_IX_8648 · SEALED
