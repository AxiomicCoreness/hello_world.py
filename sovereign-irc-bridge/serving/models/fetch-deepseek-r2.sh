#!/usr/bin/env bash
# fetch-deepseek-r2.sh — download the deepseek-r2-1.5b Q4_K_M GGUF from the
# GitHub Release (25 MB chunks), verify every chunk, reassemble, extract,
# and verify the final GGUF sha256. No tokens are used or required.
#
# Usage:
#   ./fetch-deepseek-r2.sh                 # into this script's folder (serving/models/)
#   DEST=/some/dir ./fetch-deepseek-r2.sh  # into another folder
#   KEEP_PARTS=1 ./fetch-deepseek-r2.sh    # keep the downloaded chunks afterwards
set -euo pipefail

REPO="${REPO:-AxiomicCoreness/hello_world.py}"
TAG="${TAG:-model-deepseek-r2-1.5b-q4km-v1}"
BASE="deepseek-r2-1.5b-Q4_K_M"
ARCHIVE="${BASE}.tar.gz"
GGUF="${BASE}.gguf"
GGUF_SHA256="80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1"
URL_BASE="https://github.com/${REPO}/releases/download/${TAG}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${DEST:-$SCRIPT_DIR}"
mkdir -p "$DEST"
WORK="$(mktemp -d "${DEST%/}/.fetch-deepseek-r2.XXXXXX")"
cleanup() { [ "${KEEP_PARTS:-0}" = "1" ] || rm -rf "$WORK"; }
trap cleanup EXIT

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}

fetch() { # fetch <asset-name>
  curl -fL --retry 5 --retry-delay 2 --retry-all-errors -sS -o "$WORK/$1" "$URL_BASE/$1"
}

if [ -f "$DEST/$GGUF" ] && [ "$(sha256_of "$DEST/$GGUF")" = "$GGUF_SHA256" ]; then
  echo "OK: $DEST/$GGUF already present and verified"; exit 0
fi

echo "Downloading SHA256SUMS from $URL_BASE"
fetch SHA256SUMS

mapfile -t PARTS < <(awk '{print $2}' "$WORK/SHA256SUMS" | grep -E "^${ARCHIVE//./\\.}\.part-[0-9]{3}$" | sort)
[ "${#PARTS[@]}" -gt 0 ] || { echo "ERROR: no parts listed in SHA256SUMS" >&2; exit 1; }
echo "Fetching ${#PARTS[@]} parts"

expected() { awk -v f="$1" '$2==f {print $1}' "$WORK/SHA256SUMS"; }

for p in "${PARTS[@]}"; do
  want="$(expected "$p")"
  for attempt in 1 2 3; do
    fetch "$p"
    got="$(sha256_of "$WORK/$p")"
    [ "$got" = "$want" ] && break
    echo "WARN: $p sha256 mismatch (attempt $attempt), retrying" >&2
    [ "$attempt" = 3 ] && { echo "ERROR: $p sha256 $got != $want" >&2; exit 1; }
  done
  echo "  ok $p"
done

echo "Reassembling $ARCHIVE"
cat "${PARTS[@]/#/$WORK/}" > "$WORK/$ARCHIVE"
want="$(expected "$ARCHIVE")"; got="$(sha256_of "$WORK/$ARCHIVE")"
[ "$got" = "$want" ] || { echo "ERROR: $ARCHIVE sha256 $got != $want" >&2; exit 1; }
echo "  ok $ARCHIVE $got"
for p in "${PARTS[@]}"; do rm -f "$WORK/$p"; done

echo "Extracting $GGUF"
tar -xzf "$WORK/$ARCHIVE" -C "$WORK" "$GGUF"
got="$(sha256_of "$WORK/$GGUF")"
[ "$got" = "$GGUF_SHA256" ] || { echo "ERROR: $GGUF sha256 $got != $GGUF_SHA256" >&2; exit 1; }
mv -f "$WORK/$GGUF" "$DEST/$GGUF"
echo "OK: $DEST/$GGUF sha256 $got"
