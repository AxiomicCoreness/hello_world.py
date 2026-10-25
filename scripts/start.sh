#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# Loopback Dual ASGI only. Does not fill MCP.
# Entry point: fastapi_flywheel_gearbox (local fastMCP package removed).
set -euo pipefail
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8024}"
if [ "$HOST" = "0.0.0.0" ] || [ "$HOST" = "::" ]; then
  echo "refuse wildcard — Dual ASGI is 127.0.0.1:8024" >&2
  exit 2
fi
exec python -m uvicorn fastapi_flywheel_gearbox:app --host "$HOST" --port "$PORT"
