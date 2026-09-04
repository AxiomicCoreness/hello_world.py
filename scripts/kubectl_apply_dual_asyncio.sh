#!/usr/bin/env bash
# Specification apply for k8s/dual-asyncio-cicd.yaml (9179).
# Default: client dry-run. Skip if kubectl or cluster is missing.
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
