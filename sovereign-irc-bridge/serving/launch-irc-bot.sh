#!/usr/bin/env bash
# IRC bot mode: connects OUT to IRC (TLS 6697) and answers `!llm` in one channel.
# Same /llm path as launch-6680-deepseek-r2.sh (DeepInfer 127.0.0.1:8090 → deepseek-r2 on 127.0.0.1:8085),
# so start launch-8085-deepseek-r2.sh first. No domain, no wss://, no open ports; the model stays on loopback.
# Env (see IRC_BOT.md): IRC_HOST (irc.abjects.net; TLS 6697), IRC_OWNER (optional on abjects, required on
#   Libera.Chat), IRC_PORT, IRC_TLS (IRC_TLS=0 → abjects plaintext 6669), IRC_NICK, IRC_CHANNEL,
#   IRC_SASL_PASS / IRC_NICKSERV_PASS (optional secrets, env only; SASL needed only on Libera from cloud IPs),
#   BRIDGE_DIR, RUN_DIR, PYTHON, LLM_HISTORY_PATH.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_DIR="${BRIDGE_DIR:-$(dirname "$SCRIPT_DIR")}"
RUN_DIR="${RUN_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/sovereign-bridge}"
PYTHON="${PYTHON:-python3}"
mkdir -p "$RUN_DIR"
cd "$BRIDGE_DIR"
export IRC_HOST="${IRC_HOST:-irc.abjects.net}" IRC_NICK="${IRC_NICK:-ClarkeTutorBot}" \
  IRC_CHANNEL="${IRC_CHANNEL:-#axiomiccoreness}" IRC_TLS="${IRC_TLS:-1}"
export LLM_URL="${LLM_URL:-http://127.0.0.1:8081/v1/chat/completions}" LLM_MODEL="${LLM_MODEL:-local-gguf}" \
  LLM_BACKEND="${LLM_BACKEND:-deepinfer}" LLM_FALLBACK="${LLM_FALLBACK:-clarkeyoursatee}" \
  LLM_CLARKEYOURSATEE_URL="${LLM_CLARKEYOURSATEE_URL:-http://127.0.0.1:8085/v1/chat/completions}" \
  LLM_CLARKEYOURSATEE_MODEL="${LLM_CLARKEYOURSATEE_MODEL:-deepseek-r2-1.5b}" \
  LLM_MAX_TOKENS="${LLM_MAX_TOKENS:-1024}" \
  LLM_RAW_REPLY="${LLM_RAW_REPLY:-1}" \
  LLM_HISTORY_PATH="${LLM_HISTORY_PATH:-$RUN_DIR/llm_history.jsonl}" \
  LLM_HISTORY_MAX_TOKENS="${LLM_HISTORY_MAX_TOKENS:-2500}"
exec "$PYTHON" -m src.irc_llm_bot
