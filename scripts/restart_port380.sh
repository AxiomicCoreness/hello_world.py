#!/usr/bin/env bash
# Restart Port 380 MCP uvicorn via protected /restart endpoint.
# Replaces former AWS OIDC deploy restart path.
set -euo pipefail

MCP_URL="${MCP_URL:-http://127.0.0.1:${PORT:-8000}}"
GARDEN_SECRET="${GARDEN_SECRET:-}"
REASON="${1:-manual_ops}"

echo "# restart_port380 — $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "MCP_URL=$MCP_URL reason=$REASON"

HTTP_CODE=$(curl -s -o /tmp/port380_restart.json -w "%{http_code}" -X POST "$MCP_URL/restart" \
  -H "Content-Type: application/json" \
  -H "X-Garden-Secret: $GARDEN_SECRET" \
  -d "{\"token\": \"$GARDEN_SECRET\", \"reason\": \"$REASON\"}" || echo "000")

echo "HTTP $HTTP_CODE"
cat /tmp/port380_restart.json 2>/dev/null || true
echo

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ uvicorn restart scheduled"
  exit 0
fi

echo "⚠️ remote /restart failed — attempting local process restart"
if pgrep -f "port380_mcp.py|uvicorn.*port380" >/dev/null 2>&1; then
  pkill -f "port380_mcp.py" || true
  pkill -f "uvicorn.*port380" || true
  sleep 1
  nohup python3 port380_mcp.py > /tmp/port380_mcp.log 2>&1 &
  echo "✅ local uvicorn respawned pid=$!"
else
  echo "No local port380 uvicorn process found"
  exit 1
fi
