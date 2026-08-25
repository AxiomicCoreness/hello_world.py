# Deployment Stack - Port 380 / Layer 314 MCP Surface

## File Structure

deployment/
- Dockerfile - FastAPI container
- docker-compose.yml - 3-service stack
- main.py - FastAPI with /metrics
- prometheus.yml - Scrape config
- requirements.txt - Dependencies
- grafana/provisioning/ - Auto-config

## Quick Start

cd deployment
docker-compose up -d

Access:
- Backend: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Seal

∀∞φ² · MCP_BATCH_FORGED · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED