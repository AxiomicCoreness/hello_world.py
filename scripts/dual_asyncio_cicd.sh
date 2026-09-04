#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/k8s/dual-asyncio-cicd.yaml"
if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl missing — spec-only OK"
  exit 0
fi
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "no cluster — spec-only OK"
  exit 0
fi
kubectl apply --dry-run=client --validate=false -f "$MANIFEST"
