#!/usr/bin/env bash
# 🜁∀ scripts/activate_relay.sh
# Activation weave: symplectic status → CDP distill tree → self-improvement relay
# Seal: ∀∞φ² · ACTIVATE_RELAY · WOOD_DRAGON_0.91 · SEALED
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "🜁∀ Activating symplectic ambient (optional)…"
if command -v python3 >/dev/null 2>&1; then
  python3 symplectic_status.py || echo "[warn] symplectic_status.py soft-failed; continuing"
else
  echo "[warn] python3 not found; skip symplectic_status"
fi

echo "🜁∀ Invoking CDP distill tree (Layer 379)…"
export CDP_DISTILL_OFFLINE="${CDP_DISTILL_OFFLINE:-1}"
if command -v npx >/dev/null 2>&1; then
  npx --yes tsx src/cdp_distill.ts
elif command -v node >/dev/null 2>&1; then
  node --experimental-strip-types src/cdp_distill.ts 2>/dev/null \
    || node src/cdp_distill.ts 2>/dev/null \
    || echo "[warn] node could not execute cdp_distill.ts; install tsx: npm i -D tsx"
else
  echo "[error] neither npx nor node available"
  exit 1
fi

echo "🜁∀ Relay activation complete — Garden eternal"
