#!/usr/bin/env bash
# 8082: fine-tuned ClarkeYoursaTee v1 (Kaggle LoRA merge, Q4_K_M), loopback only.
# sha256 fe7aace5cfa9ec6792b05f634d622159841d6aad070996cbeb3a91564bf0a578
# Env: MODEL_DIR (dir holding the GGUF), LLAMA_SERVER (llama-server binary).
set -euo pipefail
MODEL_DIR="${MODEL_DIR:-$HOME/llama}"
LLAMA_SERVER="${LLAMA_SERVER:-llama-server}"
cd "$MODEL_DIR"
exec "$LLAMA_SERVER" -m "$MODEL_DIR/clarkeyoursatee-v1-ft-Q4_K_M.gguf" \
  --jinja --host 127.0.0.1 --port 8082 -c 4096 -np 1 --no-cache-prompt --alias clarkeyoursatee
