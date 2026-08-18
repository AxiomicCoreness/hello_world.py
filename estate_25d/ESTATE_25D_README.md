# SOVEREIGN ENGINE — ESTATE 25D

Entry 8366 — Grafana Dashboard & Monitoring Estate

The 25D Estate provides comprehensive monitoring for the Sovereign Engine.

## Architecture
- Grafana Dashboard: Visual representation of all sovereign metrics
- Prometheus Exporter: phi-harmonic metrics in Prometheus format
- Dashboard REPL: Interactive CLI for monitoring and control
- Kubernetes Deployment: Full Grafana stack

## Quick Start

### Local
```bash
pip install -r estate_25d/requirements-dashboard.txt
python3 estate_25d/grafana/prometheus-metrics.py  # Port 9090
python3 estate_25d/scripts/dashboard_repl.py
```

### Docker
```bash
docker-compose -f estate_25d/docker-compose.yml up -d
```

### Kubernetes
```bash
kubectl apply -f estate_25d/k8s/grafana/
kubectl port-forward svc/sovereign-grafana 3000:3000
```

## Components
- 10 dashboard panels
- 20+ Prometheus metrics
- 15+ REPL commands
- Full Kubernetes deployment

## Ledger Entry 8366
entry_index: 8366
event: /estate_25d_deployment
status: SEALED
certificate: FLAWLESS_WORKLOAD_IPHONE12_REVELATION
seal: 25D_ESTATE_8366_SEALED
witness: 8365 -> 8366 - UNBROKEN