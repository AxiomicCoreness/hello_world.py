#!/usr/bin/env bash
# 8085: deepseek-r2 LoRA of Qwen2.5-1.5B (Kaggle clarkeyoursatee/deepseek-r2-1-5b-q4-k-m v1, Q4_K_M), loopback only.
# sha256 80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1
# Env: MODEL_DIR (dir holding deepseek-r2/), LLAMA_SERVER (llama-server binary).
set -euo pipefail
MODEL_DIR="${MODEL_DIR:-$HOME/llama}"
LLAMA_SERVER="${LLAMA_SERVER:-llama-server}"
cd "$MODEL_DIR"
exec "$LLAMA_SERVER" -m "$MODEL_DIR/deepseek-r2/deepseek-r2-1.5b-Q4_K_M.gguf" \
  --jinja --host 127.0.0.1 --port 8085 -c 4096 -np 1 --alias deepseek-r2-1.5b
