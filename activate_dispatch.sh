#!/usr/bin/env bash
# 🜁∀ ACTIVATE WORKLOAD DISPATCH — AUTONOMOUS BOOTSTRAP
# Usage: ./activate_dispatch.sh [--force-bootstrap]

set -euo pipefail

REPO="AxiomicCoreness/hello_world.py"
WORKFLOW_PATH=".github/workflows/oidc-handover.yml"
BRANCH="main"
LOG_DIR="./dispatch_logs"
mkdir -p "$LOG_DIR"

FORCE=0
if [[ "${1:-}" == "--force-bootstrap" ]]; then
  FORCE=1
fi

# Check for prerequisites
if ! command -v gh &>/dev/null; then
  echo "⚠️  GitHub CLI (gh) not found. Bootstrapping Python environment..."
  python3 ./sovereign_workload_bootstrap.py --mode bootstrap --target dispatch
  exit $?
fi

# If the workflow file doesn't exist locally, bootstrap it
if [[ ! -f "$WORKFLOW_PATH" ]] || [[ "$FORCE" -eq 1 ]]; then
  echo "⚠️  Workflow missing or force-bootstrap. Ensuring from Python..."
  python3 ./sovereign_workload_bootstrap.py --mode bootstrap --target workflow
fi

# Attempt to dispatch via gh
echo "🚀 Dispatching OIDC Handover via gh CLI..."
if gh workflow run oidc-handover.yml --repo "$REPO" --ref "$BRANCH" 2>&1; then
  LOG_FILE="$LOG_DIR/dispatch_$(date +%s).log"
  echo "✅ Dispatch requested. Logging to $LOG_FILE"
  gh run list --repo "$REPO" --workflow oidc-handover.yml --limit 3 > "$LOG_FILE" || true
else
  echo "❌ gh dispatch failed. Falling back to Python bootstrap/API dispatch..."
  python3 ./sovereign_workload_bootstrap.py --mode bootstrap --target api
fi
