#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# scripts/link_core.sh — symlink .container/ml_sovereign_core.py at the engine body.
set -euo pipefail

cd "$(dirname "$0")/.."

# Real implementation. Repo-root sovereign_engine.py is a compatibility shim.
TARGET="scripts/ml_sovereign_core.py"
LINK=".container/ml_sovereign_core.py"

if [[ ! -f "$TARGET" ]]; then
    printf 'missing target: %s\n' "$TARGET" >&2
    exit 1
fi

if [[ -L "$LINK" ]]; then
    rm -f "$LINK"
elif [[ -e "$LINK" ]]; then
    printf 'refusing to overwrite non-symlink: %s\n' "$LINK" >&2
    exit 1
fi

# Relative to .container/, so the stored target is ../scripts/ml_sovereign_core.py.
ln -s "../$TARGET" "$LINK"

if [[ ! -f "$LINK" ]]; then
    printf 'link does not resolve to a file: %s -> %s\n' "$LINK" "$(readlink "$LINK")" >&2
    exit 1
fi

resolved=$(readlink -f "$LINK")
expected=$(readlink -f "$TARGET")
if [[ "$resolved" != "$expected" ]]; then
    printf 'link resolved to %s, expected %s\n' "$resolved" "$expected" >&2
    exit 1
fi

printf 'linked %s -> %s\n' "$LINK" "$(readlink "$LINK")"
