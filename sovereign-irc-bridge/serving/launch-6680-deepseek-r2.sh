#!/usr/bin/env bash
# Bridge with fallback -> deepseek-r2-1.5b on 8085. Loopback 127.0.0.1:6680.
# LLM_MAX_TOKENS=1024: this R1-style model thinks first; at the 256 default the reasoning used every token and /llm showed "(empty reply)".
# Env: BRIDGE_DIR (sovereign-irc-bridge checkout), RUN_DIR (runtime state: history), PYTHON (interpreter with bridge deps).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_DIR="${BRIDGE_DIR:-$(dirname "$SCRIPT_DIR")}"
RUN_DIR="${RUN_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/sovereign-bridge}"
PYTHON="${PYTHON:-python3}"
mkdir -p "$RUN_DIR"
cd "$BRIDGE_DIR"
export LLM_URL=http://127.0.0.1:8081/v1/chat/completions LLM_MODEL=local-gguf \
  LLM_BACKEND=deepinfer LLM_FALLBACK=clarkeyoursatee \
  LLM_CLARKEYOURSATEE_URL=http://127.0.0.1:8085/v1/chat/completions \
  LLM_CLARKEYOURSATEE_MODEL=deepseek-r2-1.5b \
  LLM_MAX_TOKENS=1024 \
  LLM_RAW_REPLY=1 \
  LLM_HISTORY_PATH="${LLM_HISTORY_PATH:-$RUN_DIR/llm_history.jsonl}" \
  LLM_HISTORY_MAX_TOKENS=2500
exec "$PYTHON" -m src.cli_loopback
