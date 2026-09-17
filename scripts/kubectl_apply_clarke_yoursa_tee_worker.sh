#!/usr/bin/env bash
# SIMD batch spec apply for k8s/clarke-yoursa-tee-worker.yaml (ledger 9199).
# Default: client dry-run. Missing kubectl or cluster → exit 0.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/k8s/clarke-yoursa-tee-worker.yaml"
MODE="${1:-dry-run}"
if [ ! -f "$FILE" ]; then
  echo "missing $FILE" >&2
  exit 1
fi
if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl missing — SIMD spec-only OK"
  exit 0
fi
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "no cluster — skip apply; replicas=0 FILLED=false"
  exit 0
fi
if [ "$MODE" = "--live" ]; then
  kubectl apply -f "$FILE"
else
  kubectl apply --dry-run=client --validate=false -f "$FILE"
fi
