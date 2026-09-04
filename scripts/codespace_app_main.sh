#!/usr/bin/env bash
# Codespace / local loopback for app_main:app.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8024}"
if [ "$HOST" = "0.0.0.0" ]; then
  echo "refuse 0.0.0.0 — Dual ASGI is 127.0.0.1:8024" >&2
  exit 2
fi
exec python -m uvicorn app_main:app --host "$HOST" --port "$PORT"
