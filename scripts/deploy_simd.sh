#!/usr/bin/env bash
# Deploy / run SIMD batch step (orchestrator.simd_step)
# Usage:
#   bash scripts/deploy_simd.sh              # local phases only
#   bash scripts/deploy_simd.sh --http       # + localhost:8000 / :8080
#   BRANCH=A bash scripts/deploy_simd.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-}:$ROOT"
BRANCH="${BRANCH:-B}"
COHERENCE="${COHERENCE:-0.99}"
PHASE="${PHASE:-200.0}"
SECRET="${GARDEN_SECRET:-wood_dragon_0.91}"

echo "[simd] root=$ROOT branch=$BRANCH"

if [[ "${1:-}" == "--http" ]]; then
  python -m orchestrator.simd_step \
    --coherence "$COHERENCE" \
    --phase "$PHASE" \
    --branch "$BRANCH" \
    --base-url "${BASE_URL:-http://localhost:8000}" \
    --mcp-url "${MCP_URL:-http://localhost:8080}" \
    --secret "$SECRET"
else
  python -m orchestrator.simd_step \
    --coherence "$COHERENCE" \
    --phase "$PHASE" \
    --branch "$BRANCH" \
    --no-http
fi
