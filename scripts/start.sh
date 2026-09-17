#!/usr/bin/env bash
# Loopback Dual ASGI only. Does not fill MCP.
set -euo pipefail
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8024}"
if [ "$HOST" = "0.0.0.0" ] || [ "$HOST" = "::" ]; then
  echo "refuse wildcard — Dual ASGI is 127.0.0.1:8024" >&2
  exit 2
fi
exec python -m uvicorn fastMCP.gearbox:app --host "$HOST" --port "$PORT"
