#!/usr/bin/env bash
# 8084: OLD ClarkeYoursaTee (metadata-only derivative, NOT fine-tuned), for comparison. Loopback only.
# sha256 982743f8000399cd1d674aa6f7a7578b1b91a0cc1f5308dc2fa6bda5a5753cb8
# Env: MODEL_DIR (dir holding the GGUF), LLAMA_SERVER (llama-server binary).
set -euo pipefail
MODEL_DIR="${MODEL_DIR:-$HOME/llama}"
LLAMA_SERVER="${LLAMA_SERVER:-llama-server}"
cd "$MODEL_DIR"
exec "$LLAMA_SERVER" -m "$MODEL_DIR/ClarkeYoursaTee-1.5B-Q4_K_M.gguf" \
  --jinja --host 127.0.0.1 --port 8084 -c 4096 -np 1 --no-cache-prompt --alias clarkeyoursatee-old
