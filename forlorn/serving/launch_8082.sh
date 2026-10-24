#!/usr/bin/env bash
# Serve ClarkeYoursaTee on loopback only (Cosmic Alignment: never 0.0.0.0).
set -euo pipefail
# -np 1 --no-cache-prompt: one slot and no KV prompt reuse, so temperature-0 replies are
# reproducible run to run (with 4 slots and a shared prompt cache the evals flipped between runs).
LLAMA_SERVER="${LLAMA_SERVER:-/workspace/llama/llama-b11840/llama-server}"
MODEL="${MODEL:-/workspace/llama/ClarkeYoursaTee-1.5B-Q4_K_M.gguf}"
PORT="${PORT:-8082}"
CTX="${CTX:-4096}"
exec "$LLAMA_SERVER" -m "$MODEL" --jinja --host 127.0.0.1 --port "$PORT" -c "$CTX" -np 1 --no-cache-prompt --alias clarkeyoursatee
