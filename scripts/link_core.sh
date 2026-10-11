#!/usr/bin/env bash
# scripts/link_core.sh — point .container/ at the root engine.
set -euo pipefail

cd "$(dirname "$0")/.."

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

ln -s "../$TARGET" "$LINK"
printf 'linked %s -> %s\n' "$LINK" "$(readlink "$LINK")"
