#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export GARDEN_SECRET="${GARDEN_SECRET:-your_secret_here}"
export MCP_CONNECTOR_URL="${MCP_CONNECTOR_URL:-http://localhost:380}"
export MCP_URL="${MCP_URL:-http://localhost:380}"
export GROK_API_KEY="${GROK_API_KEY:-}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
export MISTRAL_API_KEY="${MISTRAL_API_KEY:-}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

exec uvicorn port380_mcp:app --host "${PORT380_HOST:-127.0.0.1}" --port "${PORT380_PORT:-380}" "$@"
