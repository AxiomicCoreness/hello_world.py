#!/usr/bin/env bash
# Alias name requested 2026-09-04. Body matches 9188 wrapper.
# Does not rewrite k8s/dual-asyncio-cicd.yaml (9179).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/scripts/dual_asyncio_cicd.sh"
