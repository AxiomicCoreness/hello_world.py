#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# tools/paper-mcp/launch.sh — defaults from config.env, then scripts/paper_mcp.sh.
# Values already in the environment are kept.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
CONFIG="$HERE/config.env"

if [[ -f "$CONFIG" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
            ''|\#*) continue ;;
        esac
        key="${line%%=*}"
        val="${line#*=}"
        if [[ -z "${!key:-}" ]]; then
            export "$key=$val"
        fi
    done < "$CONFIG"
fi

exec bash "$ROOT/scripts/paper_mcp.sh" "$@"
