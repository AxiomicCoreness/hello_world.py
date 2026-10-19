---
title: Port 380 Prebuild
name: port380-prebuild
type: text/markdown
---

# Port 380 Prebuild

**Type**: Canvas
**Category**: Build notes
**Status**: ACTIVE

## Overview
What has to be in place before building and serving the Port-380 surfaces,
as recorded on `main`.

## Java connectome loader
- JDK 17 (`pom.xml`: `maven.compiler.release` 17), Maven, JUnit 5.10.2.
- 21 JUnit tests under `src/test/java/com/fruitfly/brain/`.
- `src/main/resources/HHMIJaneliaMap.xml` is a 3-neuron placeholder and is
  bundled into the jar by `mvn package`.
- `SovereignMain --connectome-file PATH` loads the network from XML; bad
  arguments exit with code 2.

## Python servers and bindings
- `app.main:app` (FastAPI) serves on 8000 with `GET /health`
  (`docker-compose.yml`).
- `port380_mcp.py` binds `BIND_HOST` (default `127.0.0.1`) and uses `PORT`,
  then `MCP_PORT`, then 380. In Kubernetes the container listens on 8380 and
  the Service exposes 380.
- Refuses to start without `GARDEN_SECRET`. `--check-config [--json]`
  validates host, port and secret without binding; exits 0 or 1.
- Public health routes: `/health`, `/healthz`.
- Minimal install: `requirements-mcp.txt`.

## Pentad rank (Port-380 FAL gate)
- Rank r ∈ {−2, −1, 0, +1, +2}; −1/0/+1 unchanged, ±2 = 2× the ±1 scaling,
  explicit override only. See `docs/pentad_rank.md` (`fe9fc38`).

## Verification
- [x] 21 JUnit tests
- [x] 65 tests in `tests/test_port380_pentad.py`
- [x] `--check-config` never binds a port
