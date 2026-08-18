#!/usr/bin/env bash
# Build + push axiomic/sovereign-engine:latest ALWAYS from main.
# Feature / casual branches are ignored for the image tag.
#
# Usage:
#   bash scripts/docker_build_push_main.sh
#   bash scripts/docker_build_push_main.sh --no-cache
#   bash scripts/docker_build_push_main.sh --local-only   # build, do not push
#
# Ledger 8818 · WOOD_DRAGON_0.91
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IMG="${IMAGE:-axiomic/sovereign-engine:latest}"
REF="main"
NO_CACHE=()
PUSH=1

for arg in "$@"; do
  case "$arg" in
    --no-cache) NO_CACHE=(--no-cache) ;;
    --local-only) PUSH=0 ;;
    --help|-h)
      sed -n '1,20p' "$0"
      exit 0
      ;;
  esac
done

# Record whatever branch the shell was on, then force main for the build context
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo "[docker] shell branch was: $CURRENT_BRANCH (ignored)"
echo "[docker] image source ref: $REF only"

# Ensure we have main tips (no checkout required if already on main with clean tree)
git fetch origin "$REF" --quiet 2>/dev/null || true

if git rev-parse --verify "origin/$REF" >/dev/null 2>&1; then
  MAIN_SHA="$(git rev-parse "origin/$REF")"
elif git rev-parse --verify "$REF" >/dev/null 2>&1; then
  MAIN_SHA="$(git rev-parse "$REF")"
else
  echo "[docker] ERROR: cannot resolve $REF" >&2
  exit 1
fi

echo "[docker] main SHA: $MAIN_SHA"
echo "[docker] building $IMG from git archive of $REF"

# Build from main tree only — not the working branch dirty tree
TMPDIR_BUILD="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR_BUILD"; }
trap cleanup EXIT

git archive --format=tar "$MAIN_SHA" | tar -x -C "$TMPDIR_BUILD"

docker build "${NO_CACHE[@]}" -t "$IMG" -f "$TMPDIR_BUILD/Dockerfile" "$TMPDIR_BUILD"

echo "[docker] build OK: $IMG"

if [[ "$PUSH" -eq 1 ]]; then
  docker push "$IMG"
  echo "[docker] push OK: $IMG"
else
  echo "[docker] --local-only: skip push"
fi

echo "[docker] done (branch $CURRENT_BRANCH was not used as image source)"
