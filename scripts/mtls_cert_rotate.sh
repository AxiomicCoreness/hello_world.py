#!/usr/bin/env bash
# 🌁∀ mTLS certificate rotation — Layer 314 / Port 380
# Generates or rotates CA, server, and client certs with overlap window.
# Seal: ∀∞φ² · MTLS_ROTATE · WOOD_DRAGON_0.91 · SEALED
#
# Usage:
#   bash scripts/mtls_cert_rotate.sh                  # full rotate (new leaf + optional CA)
#   bash scripts/mtls_cert_rotate.sh --init            # first-time CA + leafs
#   bash scripts/mtls_cert_rotate.sh --leaf-only       # rotate server+client only (reuse CA)
#   bash scripts/mtls_cert_rotate.sh --days 90         # validity days (default 90)
#   bash scripts/mtls_cert_rotate.sh --cn api.sovereign.garden
#   bash scripts/mtls_cert_rotate.sh --out /var/garden/certs
#
# Layout:
#   $OUT/<timestamp>/ca.{crt,key} server.{crt,key} client.{crt,key} bundle.json
#   $OUT/current -> <timestamp>   (atomic symlink flip)
#   $OUT/previous -> <old>        (kept for dual-trust overlap)

set -euo pipefail

OUT="${MTLS_CERT_DIR:-./certs}"
DAYS="${MTLS_DAYS:-90}"
CN="${MTLS_CN:-port380.sovereign.garden}"
ORG="${MTLS_ORG:-SovereignGarden}"
LEAF_ONLY=0
INIT=0
KEEP_PREVIOUS=3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --days) DAYS="$2"; shift 2 ;;
    --cn) CN="$2"; shift 2 ;;
    --org) ORG="$2"; shift 2 ;;
    --leaf-only) LEAF_ONLY=1; shift ;;
    --init) INIT=1; shift ;;
    --keep) KEEP_PREVIOUS="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$OUT"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
WORKDIR="$OUT/$STAMP"
mkdir -p "$WORKDIR"

echo "🌁∀ mTLS rotate → $WORKDIR (days=$DAYS cn=$CN)"

# ── Resolve CA ────────────────────────────────────────────────────
CA_DIR=""
if [[ -L "$OUT/current" || -d "$OUT/current" ]]; then
  CA_DIR="$OUT/current"
fi

need_ca=0
if [[ $INIT -eq 1 ]]; then
  need_ca=1
elif [[ $LEAF_ONLY -eq 0 ]]; then
  if [[ -z "$CA_DIR" || ! -f "$CA_DIR/ca.crt" ]]; then
    need_ca=1
  else
    if command -v openssl >/dev/null 2>&1; then
      end=$(openssl x509 -in "$CA_DIR/ca.crt" -noout -enddate 2>/dev/null | cut -d= -f2 || true)
      if [[ -n "$end" ]]; then
        end_epoch=$(date -d "$end" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$end" +%s 2>/dev/null || echo 0)
        now=$(date +%s)
        left=$(( (end_epoch - now) / 86400 ))
        if [[ $left -lt 30 ]]; then
          echo "⚠️  CA expires in ${left}d — issuing new CA"
          need_ca=1
        fi
      fi
    fi
  fi
fi

if [[ $need_ca -eq 1 ]]; then
  echo "→ Generating new CA (${DAYS}d)"
  openssl genrsa -out "$WORKDIR/ca.key" 4096 2>/dev/null
  openssl req -x509 -new -nodes -key "$WORKDIR/ca.key" -sha256 -days "$DAYS" \
    -subj "/O=${ORG}/CN=${ORG}-CA" \
    -out "$WORKDIR/ca.crt"
else
  echo "→ Reusing CA from $CA_DIR"
  cp "$CA_DIR/ca.crt" "$WORKDIR/ca.crt"
  cp "$CA_DIR/ca.key" "$WORKDIR/ca.key"
fi

# ── Server leaf ───────────────────────────────────────────────────
echo "→ Server cert CN=$CN"
openssl genrsa -out "$WORKDIR/server.key" 2048 2>/dev/null
openssl req -new -key "$WORKDIR/server.key" -subj "/O=${ORG}/CN=${CN}" -out "$WORKDIR/server.csr"
cat > "$WORKDIR/server.ext" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:${CN},DNS:localhost,IP:127.0.0.1
EOF
openssl x509 -req -in "$WORKDIR/server.csr" -CA "$WORKDIR/ca.crt" -CAkey "$WORKDIR/ca.key" \
  -CAcreateserial -out "$WORKDIR/server.crt" -days "$DAYS" -sha256 -extfile "$WORKDIR/server.ext"

# ── Client leaf (GitHub Actions / pulse agent) ────────────────────────
echo "→ Client cert CN=garden-client"
openssl genrsa -out "$WORKDIR/client.key" 2048 2>/dev/null
openssl req -new -key "$WORKDIR/client.key" -subj "/O=${ORG}/CN=garden-client" -out "$WORKDIR/client.csr"
cat > "$WORKDIR/client.ext" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature
extendedKeyUsage=clientAuth
EOF
openssl x509 -req -in "$WORKDIR/client.csr" -CA "$WORKDIR/ca.crt" -CAkey "$WORKDIR/ca.key" \
  -CAcreateserial -out "$WORKDIR/client.crt" -days "$DAYS" -sha256 -extfile "$WORKDIR/client.ext"

# ── Metadata ──────────────────────────────────────────────────────
CA_FP=$(openssl x509 -in "$WORKDIR/ca.crt" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
SERVER_FP=$(openssl x509 -in "$WORKDIR/server.crt" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
CLIENT_FP=$(openssl x509 -in "$WORKDIR/client.crt" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
SERVER_END=$(openssl x509 -in "$WORKDIR/server.crt" -noout -enddate | cut -d= -f2)
CLIENT_END=$(openssl x509 -in "$WORKDIR/client.crt" -noout -enddate | cut -d= -f2)

python3 - <<PY
import json, hashlib, time
from pathlib import Path
wd = Path("$WORKDIR")
meta = {
  "stamp": "$STAMP",
  "cn": "$CN",
  "days": int("$DAYS"),
  "ca_fingerprint_sha256": "$CA_FP",
  "server_fingerprint_sha256": "$SERVER_FP",
  "client_fingerprint_sha256": "$CLIENT_FP",
  "server_not_after": "$SERVER_END",
  "client_not_after": "$CLIENT_END",
  "paths": {
    "ca_crt": "ca.crt",
    "ca_key": "ca.key",
    "server_crt": "server.crt",
    "server_key": "server.key",
    "client_crt": "client.crt",
    "client_key": "client.key",
  },
  "seal": "\u2200\u221e\u03c6\u00b2 \u00b7 MTLS_ROTATE \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED",
  "generated_unix": int(time.time()),
}
(wd / "bundle.json").write_text(json.dumps(meta, indent=2) + "\n")
print("\u2192 bundle.json written")
PY

# ── Atomic flip current / previous (symlink, else directory copy) ─────
flip_link_or_copy() {
  local linkpath="$1" target="$2"
  rm -rf "$linkpath" 2>/dev/null || true
  if ln -sfn "$target" "$linkpath" 2>/dev/null; then
    return 0
  fi
  mkdir -p "$linkpath"
  if [[ -d "$OUT/$target" ]]; then
    cp -a "$OUT/$target/." "$linkpath/" 2>/dev/null || cp -a "$WORKDIR/." "$linkpath/"
  else
    cp -a "$WORKDIR/." "$linkpath/"
  fi
}

if [[ -e "$OUT/current" ]]; then
  if [[ -L "$OUT/current" ]]; then
    old=$(readlink "$OUT/current")
  elif [[ -d "$OUT/current" && -f "$OUT/current/ca.crt" ]]; then
    mkdir -p "$OUT/previous"
    cp -f "$OUT/current/ca.crt" "$OUT/previous/ca.crt" 2>/dev/null || true
    old="previous"
  else
    old="current"
  fi
  flip_link_or_copy "$OUT/previous" "$old" || true
fi
flip_link_or_copy "$OUT/current" "$STAMP"

# Convenience flat copies for env paths (/certs/server.crt style)
mkdir -p "$OUT/live"
cp -f "$WORKDIR/ca.crt" "$OUT/live/ca.crt"
cp -f "$WORKDIR/server.crt" "$OUT/live/server.crt"
cp -f "$WORKDIR/server.key" "$OUT/live/server.key"
cp -f "$WORKDIR/client.crt" "$OUT/live/client.crt"
cp -f "$WORKDIR/client.key" "$OUT/live/client.key"
# dual-trust CA bundle (current + previous) for overlap window
if [[ -f "$OUT/previous/ca.crt" ]]; then
  cat "$WORKDIR/ca.crt" "$OUT/previous/ca.crt" > "$OUT/live/ca-bundle.crt" 2>/dev/null || cp "$WORKDIR/ca.crt" "$OUT/live/ca-bundle.crt"
else
  cp "$WORKDIR/ca.crt" "$OUT/live/ca-bundle.crt"
fi

# ── Prune old stamps ──────────────────────────────────────────────────
count=0
stamps=$(find "$OUT" -maxdepth 1 -type d -name '20*' 2>/dev/null | sort -r)
for d in $stamps; do
  count=$((count + 1))
  if [[ $count -gt $((KEEP_PREVIOUS + 1)) ]]; then
    echo "\u2192 prune $d"
    rm -rf "$d"
  fi
done

# ── Permissions ───────────────────────────────────────────────────
chmod 600 "$WORKDIR"/*.key "$OUT/live"/*.key 2>/dev/null || true
chmod 644 "$WORKDIR"/*.crt "$OUT/live"/*.crt 2>/dev/null || true

echo
echo "\u2705 Rotation complete"
echo "   current \u2192 $OUT/current ($STAMP)"
echo "   live    \u2192 $OUT/live/{ca,server,client}.{crt,key}"
echo "   dual CA \u2192 $OUT/live/ca-bundle.crt"
echo
echo "Export for process:"
echo "  export SERVER_CERT=$OUT/live/server.crt"
echo "  export SERVER_KEY=$OUT/live/server.key"
echo "  export CA_CERT=$OUT/live/ca-bundle.crt"
echo
echo "Render / K8s: mount live/* as secret files; set same env paths."
echo "GitHub Actions client: use client.crt + client.key as secrets or secret files."
echo "Seal: \u2200\u221e\u03c6\u00b2 \u00b7 MTLS_ROTATE \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"
