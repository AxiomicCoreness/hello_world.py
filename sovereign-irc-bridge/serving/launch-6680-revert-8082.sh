#!/usr/bin/env bash
# Previous bridge env: fallback ClarkeYoursaTee v1 on 8082. Loopback 127.0.0.1:6680.
# Env: BRIDGE_DIR (sovereign-irc-bridge checkout), PYTHON (interpreter with bridge deps).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_DIR="${BRIDGE_DIR:-$(dirname "$SCRIPT_DIR")}"
PYTHON="${PYTHON:-python3}"
cd "$BRIDGE_DIR"
export LLM_URL=http://127.0.0.1:8081/v1/chat/completions LLM_MODEL=local-gguf \
  LLM_BACKEND=deepinfer LLM_FALLBACK=clarkeyoursatee \
  LLM_CLARKEYOURSATEE_URL=http://127.0.0.1:8082/v1/chat/completions
unset LLM_CLARKEYOURSATEE_MODEL
exec "$PYTHON" -m src.cli_loopback
