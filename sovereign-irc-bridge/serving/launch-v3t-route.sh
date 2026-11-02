#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# Authenticated v3t /llm route on 127.0.0.1:8087 -> llama-server 127.0.0.1:8085. Loopback only.
# History DB stays outside the repo (mode 600). Public reach only via the bridge/tunnel in front.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export V3T_HOST="${V3T_HOST:-127.0.0.1}"
case "$V3T_HOST" in 127.0.0.1|::1|localhost) ;; *) echo "refusing V3T_HOST=$V3T_HOST (loopback only)" >&2; exit 2;; esac
export V3T_PORT="${V3T_PORT:-8087}"
export V3T_DB="${V3T_DB:-/workspace/bridge-serving/v3t/v3t_history.sqlite3}"
export V3T_MODEL_PATH="${V3T_MODEL_PATH:-/workspace/llama/v3t/ClarkeYoursaTee-2B-v3-Q4_K_M.gguf}"
cd "$HERE"
exec python3 -I src/v3t_route.py "$@"
