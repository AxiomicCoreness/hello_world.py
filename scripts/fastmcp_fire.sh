#!/usr/bin/env bash
# Machine-readable FastMCP firing sequence runner (stub-safe).
# Does not start patent daemons. Does not auto-file.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export MCP_BIND_HOST="${MCP_BIND_HOST:-127.0.0.1}"
export MCP_PORT="${MCP_PORT:-13800}"
export MCP_NAMESPACE="${MCP_NAMESPACE:-sovereign-garden}"
export MCP_SELFIMPROVE="${MCP_SELFIMPROVE:-0}"
export AUTO_FILE="${AUTO_FILE:-0}"

echo "[10] env OK host=$MCP_BIND_HOST port=$MCP_PORT ns=$MCP_NAMESPACE"
echo "[20] check-config"
python mcp/port380_mcp.py --check-config
echo "[30] math_origin"
python -c "from math_origin import verify_canonical_19; ok,cw=verify_canonical_19(); assert ok; print(cw.payload_segment())"
echo "[40] FastAPI surface is separate (not MCP)"
echo "[60] patent automation: SKIPPED (AUTO_FILE=$AUTO_FILE)"
echo "[70] selfimprove: SKIPPED (MCP_SELFIMPROVE=$MCP_SELFIMPROVE)"

if [[ "${START_MCP_DAEMON:-0}" == "1" ]]; then
  echo "[50] starting MCP daemon on ${MCP_BIND_HOST}:${MCP_PORT}"
  exec python mcp/port380_mcp.py
fi

echo "✅ FastMCP firing sequence complete (stub; no live bind unless START_MCP_DAEMON=1)"
