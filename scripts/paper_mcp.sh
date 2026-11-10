#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# scripts/paper_mcp.sh — stdio or loopback HTTP for python -m paper_mcp.
# Bind is 127.0.0.1 only. PAPER_MCP_ROOT is forwarded when set.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-serve}"
if [[ $# -gt 0 ]]; then
    shift
fi

BIND="${PAPER_MCP_BIND:-${BIND_HOST:-${HOST:-127.0.0.1}}}"
PORT="${PAPER_MCP_PORT:-${PORT:-8765}}"
PY="${PYTHON:-python3}"

usage() {
    printf 'usage: %s {serve|serve-http} [paper_mcp args...]\n' "$0" >&2
    printf '  serve       MCP JSON-RPC on stdio (default)\n' >&2
    printf '  serve-http  GET /healthz and POST /mcp on 127.0.0.1\n' >&2
    printf 'Env: PAPER_MCP_ROOT, PAPER_MCP_PORT (or PORT), PYTHON\n' >&2
    printf 'HOST / BIND_HOST / PAPER_MCP_BIND must be 127.0.0.1 or localhost.\n' >&2
}

case "$MODE" in
    -h|--help|help)
        usage
        exit 0
        ;;
    serve|stdio|serve-http|http)
        ;;
    *)
        usage
        exit 2
        ;;
esac

case "$BIND" in
    127.0.0.1|localhost)
        ;;
    *)
        printf 'FATAL: refuse bind host %s; only 127.0.0.1 (or localhost) is allowed\n' "$BIND" >&2
        exit 1
        ;;
esac

case "$PORT" in
    ''|*[!0-9]*)
        printf 'FATAL: PORT must be an integer 1-65535, got %s\n' "$PORT" >&2
        exit 1
        ;;
esac
if [[ "$PORT" -lt 1 || "$PORT" -gt 65535 ]]; then
    printf 'FATAL: PORT must be an integer 1-65535, got %s\n' "$PORT" >&2
    exit 1
fi

if ! "$PY" -c 'import paper_mcp' >/dev/null 2>&1; then
    printf 'paper_mcp is not importable on this checkout\n' >&2
    exit 1
fi

ROOT_ARGS=()
if [[ -n "${PAPER_MCP_ROOT:-}" ]]; then
    ROOT_ARGS=(--root "$PAPER_MCP_ROOT")
fi

case "$MODE" in
    serve|stdio)
        exec "$PY" -m paper_mcp "${ROOT_ARGS[@]}" serve "$@"
        ;;
    serve-http|http)
        exec "$PY" -m paper_mcp "${ROOT_ARGS[@]}" serve-http --bind 127.0.0.1 --port "$PORT" "$@"
        ;;
esac
