#!/usr/bin/env bash
# 8085: deepseek-r2 LoRA of Qwen2.5-1.5B (Kaggle clarkeyoursatee/deepseek-r2-1-5b-q4-k-m v1, Q4_K_M), loopback only.
# sha256 80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1
# Env: MODEL_DIR (default: ./models next to this script), LLAMA_SERVER (llama-server binary).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="${MODEL_DIR:-$SCRIPT_DIR/models}"
LLAMA_SERVER="${LLAMA_SERVER:-llama-server}"
MODEL_FILE="$MODEL_DIR/deepseek-r2-1.5b-Q4_K_M.gguf"
EXPECTED_SHA256=80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1
if [ ! -f "$MODEL_FILE" ]; then
  echo "error: $MODEL_FILE not found." >&2
  echo "Download deepseek-r2-1.5b-Q4_K_M.gguf from https://www.kaggle.com/models/clarkeyoursatee/deepseek-r2-1-5b-q4-k-m and place it in $MODEL_DIR (see models/README.md)." >&2
  exit 1
fi
if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$MODEL_FILE" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  actual="$(shasum -a 256 "$MODEL_FILE" | awk '{print $1}')"
else
  echo "error: neither sha256sum nor shasum found; cannot verify $MODEL_FILE." >&2
  exit 1
fi
if [ "$actual" != "$EXPECTED_SHA256" ]; then
  echo "error: sha256 mismatch for $MODEL_FILE" >&2
  echo "  expected $EXPECTED_SHA256" >&2
  echo "  actual   $actual" >&2
  exit 1
fi
cd "$MODEL_DIR"
exec "$LLAMA_SERVER" -m "$MODEL_FILE" \
  --jinja --host 127.0.0.1 --port 8085 -c 4096 -np 1 --alias deepseek-r2-1.5b
