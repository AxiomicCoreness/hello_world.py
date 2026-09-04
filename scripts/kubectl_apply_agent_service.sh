#!/usr/bin/env bash
# Specification apply for k8s/agent-service.yaml (ledger 9164).
# Default: client dry-run. Live apply only with --live and a cluster.
set -euo pipefail
FILE="k8s/agent-service.yaml"
MODE="${1:-dry-run}"
if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl missing — control layer records spec only"
  exit 0
fi
if [ ! -f "$FILE" ]; then
  echo "missing $FILE" >&2
  exit 1
fi
if [ "$MODE" = "--live" ]; then
  kubectl apply -f "$FILE"
else
  kubectl apply --dry-run=client -f "$FILE"
fi
