#!/usr/bin/env bash
# fetch-deepseek-r2.sh — download the pinned deepseek-r2 Q4_K_M GGUF from its
# GitHub Release. MODEL_PIN.json picks the file, tag, size and sha256 (currently the
# unevaluated 1.8B); the constants below are the 1.5B fallback (same as MODEL_PIN.1p5b.json).
# Tries the single joined GGUF asset first and verifies its sha256; if it is missing or
# does not match and the pin has parts (1.5B: 42 x 25 MB chunks), verifies every chunk,
# reassembles, extracts, and verifies the final GGUF sha256. No tokens are used.
#
# Usage:
#   ./fetch-deepseek-r2.sh                 # into this script's folder (serving/models/)
#   DEST=/some/dir ./fetch-deepseek-r2.sh  # into another folder
#   KEEP_PARTS=1 ./fetch-deepseek-r2.sh    # keep the downloaded chunks afterwards
#   SKIP_SINGLE=1 ./fetch-deepseek-r2.sh   # skip the single-file asset, use the parts only
#   PIN=./MODEL_PIN.1p5b.json ./fetch-deepseek-r2.sh   # fall back to the 1.5B pin
set -euo pipefail

REPO="${REPO:-AxiomicCoreness/hello_world.py}"
TAG="${TAG:-model-deepseek-r2-1.5b-q4km-v1}"
BASE="deepseek-r2-1.5b-Q4_K_M"
GGUF_SHA256="80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1"
GGUF_SIZE="1117320640"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# MODEL_PIN.json (next to this script) is the source of truth; the constants above are fallbacks.
PIN="${PIN:-$SCRIPT_DIR/MODEL_PIN.json}"
pin_get() { sed -n "s/^ *\"$1\": *\"\{0,1\}\([^\",]*\)\"\{0,1\},\{0,1\} *$/\1/p" "$PIN" | head -n1; }
if [ -f "$PIN" ]; then
  v="$(pin_get gguf_sha256)"; [ -n "$v" ] && GGUF_SHA256="$v"
  v="$(pin_get size)";        [ -n "$v" ] && GGUF_SIZE="$v"
  v="$(pin_get release_tag)"; [ -n "$v" ] && TAG="$v"
  v="$(pin_get file)";        [ -n "$v" ] && BASE="${v%.gguf}"
  v="$(pin_get parts)";       [ -n "$v" ] && PIN_PARTS="$v"
  echo "Using pin $PIN ($BASE.gguf, sha256 $GGUF_SHA256, size $GGUF_SIZE)"
fi
ARCHIVE="${BASE}.tar.gz"
GGUF="${BASE}.gguf"
URL_BASE="https://github.com/${REPO}/releases/download/${TAG}"
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

# 1) single joined GGUF asset (uploaded by the join-gguf-release workflow)
if [ "${SKIP_SINGLE:-0}" != "1" ]; then
  echo "Trying single-file asset $URL_BASE/$GGUF"
  if fetch "$GGUF"; then
    got="$(sha256_of "$WORK/$GGUF")"
    if [ "$got" = "$GGUF_SHA256" ]; then
      mv -f "$WORK/$GGUF" "$DEST/$GGUF"
      echo "OK: $DEST/$GGUF sha256 $got (single-file asset)"; exit 0
    fi
    echo "WARN: single-file $GGUF sha256 $got != $GGUF_SHA256; falling back to parts" >&2
  else
    echo "WARN: single-file $GGUF not downloadable; falling back to parts" >&2
  fi
  rm -f "$WORK/$GGUF"
fi

# 2) fallback: part reassembly (only when the pin publishes parts)
if [ "${PIN_PARTS:-42}" = "0" ]; then
  echo "ERROR: $GGUF single-file asset failed and pin $PIN has no parts; nothing installed" >&2
  echo "       (to fall back to 1.5B: PIN=$SCRIPT_DIR/MODEL_PIN.1p5b.json $0)" >&2
  exit 1
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
