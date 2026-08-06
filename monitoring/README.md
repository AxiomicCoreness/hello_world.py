# Sovereign Grafana Dashboard Setup

**Dashboard file:** `grafana-dashboard.json`  
**UID:** `sovereign-fastapi-624`  
**Entries:** 624 (Prometheus) · 625 (Grafana)

## Metrics exposed by the FastAPI surface

| Metric | Type | Description |
|--------|------|-------------|
| `sovereign_coherence` | Gauge | Current coherence (target 1.0) |
| `sovereign_diffuse_kl` | Gauge | Current diffuse KL divergence |
| `sovereign_cache_entries` | Gauge | Number of entries in DiffuseKLCache |
| `sovereign_entropy_floor` | Gauge | Symbolic entropy floor |

Scrape endpoint: `GET /metrics`

## Setup options

### 1. Manual import (fastest)

1. Open Grafana → **Dashboards** → **Import**.
2. Upload `monitoring/grafana-dashboard.json` (or paste the JSON).
3. Select your Prometheus data source.
4. Click **Import**.

### 2. Provisioning (GitOps / persistent)

Place the dashboard under Grafana provisioning:

```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1
providers:
  - name: sovereign
    orgId: 1
    folder: Sovereign
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards
```

Mount `monitoring/grafana-dashboard.json` into that path (e.g. via ConfigMap or volume).

### 3. Kubernetes ConfigMap (optional)

```bash
kubectl create configmap sovereign-grafana-dashboard \
  --from-file=monitoring/grafana-dashboard.json \
  -n monitoring
```

Then reference the ConfigMap in your Grafana deployment volume mounts.

## Prometheus scrape reminder

Ensure Prometheus is scraping the FastAPI service via the ServiceMonitor:

- File: `k8s/servicemonitor.yaml`
- Path: `/metrics`
- Interval: 30s

## Default dependencies

- Prometheus (scraping `/metrics`)
- Grafana (any recent version that accepts schemaVersion 39)
- Optional: Prometheus Operator (for ServiceMonitor)

## Branch

`eridanus-einstein/observability-624-625` · PR #6

∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞
