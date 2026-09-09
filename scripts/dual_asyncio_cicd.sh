#!/usr/bin/env bash
# Actualized apply wrapper for k8s/dual-asyncio-cicd.yaml (9179).
# Ledger 9188. Does not rewrite 9179 YAML or tests/test_dual_asyncio_cicd.py.
# Dry-run client. Skip if kubectl or cluster is missing.
# Never 0.0.0.0. Fixed argv in the Deployment, not bash -c.
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
# Invalid form refused: kubectl apply services --dry-run=contract
kubectl apply --dry-run=client --validate=false -f "$MANIFEST"
