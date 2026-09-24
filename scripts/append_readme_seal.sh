#!/usr/bin/env bash
# 🜁∀∞φ² · APPEND_README_SEAL · WOOD_DRAGON_GATE · SEALED
#
# Appends README_SEAL_BLOCK.md to every README.md in the tree that does not
# already carry the marker comment. Idempotent.
#
# Usage:
#   bash scripts/append_readme_seal.sh           # dry-run
#   bash scripts/append_readme_seal.sh --apply   # actually append

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BLOCK="${REPO_ROOT}/README_SEAL_BLOCK.md"

MARKER="🜁∀∞φ² · README_SEAL_BLOCK · WOOD_DRAGON_GATE · SEALED"

APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    -h|--help)
      sed -n "3,12p" "$0" | sed "s/^# \{0,1\}//"
      exit 0
      ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [ ! -f "$BLOCK" ]; then
  echo "❌ missing block file: $BLOCK" >&2
  exit 1
fi

FOUND=0
SKIPPED=0
APPENDED=0

while IFS= read -r -d ''; do
  FOUND=$((FOUND + 1))

  if grep -qF "$MARKER" "$readme"; then
    echo "⏭  already sealed — ${readme#${REPO_ROOT}/}"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if [ "$APPLY" = "1" ]; then
    if [ -n "$(tail -c 1 "$readme")" ]; then
      printf '\n' >> "$readme"
    fi
    cat "$BLOCK" >> "$readme"
    echo "✍️  appended — ${readme#${REPO_ROOT}/}"
    APPENDED=$((APPENDED + 1))
  else
    echo "→  [dry-run] would append to — ${readme#${REPO_ROOT}/}"
    APPENDED=$((APPENDED + 1))
  fi
done < <(find "$REPO_ROOT" \
           -type f -name 'README.md' \
           -not -path '*/.git/*' \
           -not -path '*/node_modules/*' \
           -not -path '*/.venv/*' \
           -not -path '*/venv/*' \
           -print0 | sort -z)

echo
echo "  README.md files found : $FOUND"
echo "  already sealed        : $SKIPPED"
if [ "$APPLY" = "1" ]; then
  echo "  appended              : $APPENDED"
else
  echo "  would append          : $APPENDED"
  echo "  pass --apply to commit the changes"
fi

echo
echo "∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞"
