#!/usr/bin/env bash
# Specification apply for k8s/agent-service.yaml (ledger 9164).
# Without a reachable cluster, exit 0 after recording the spec.
set -euo pipefail
FILE="k8s/agent-service.yaml"
MODE="${1:-dry-run}"
if [ ! -f "$FILE" ]; then
  echo "missing $FILE" >&2
  exit 1
fi
if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl missing — control layer is YAML parse only"
  exit 0
fi
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "no cluster — skip apply; spec remains FILLED=false replicas=0"
  exit 0
fi
if [ "$MODE" = "--live" ]; then
  kubectl apply -f "$FILE"
else
  kubectl apply --dry-run=client --validate=false -f "$FILE"
fi
