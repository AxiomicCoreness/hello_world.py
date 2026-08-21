#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ MTLS CERT ROTATE — ENTRY 8821
#
# mTLS certificate rotation — Layer 314 / Port 380
# Generates or rotates CA, server, and client certs with overlap window.
#
# Usage:
#   bash scripts/mtls_cert_rotate.sh                  # full rotate (new leaf + optional CA)
#   bash scripts/mtls_cert_rotate.sh --init            # first-time CA + leafs
#   bash scripts/mtls_cert_rotate.sh --leaf-only       # rotate server+client only (reuse CA)
#   bash scripts/mtls_cert_rotate.sh --days 90         # validity days (default 90)
#   bash scripts/mtls_cert_rotate.sh --cn api.sovereign.garden
#   bash scripts/mtls_cert_rotate.sh --out /var/garden/certs
#   bash scripts/mtls_cert_rotate.sh --keep 5          # keep 5 previous stamps
#   bash scripts/mtls_cert_rotate.sh --dry-run
#
# Integration with:
#   - OpenSSL (certificate generation)
#   - Kubernetes (secrets, deployments)
#   - mTLS (quantum/mtls_cert_lifecycle.py)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Layout:
#   $OUT/<timestamp>/ca.{crt,key} server.{crt,key} client.{crt,key} bundle.json
#   $OUT/current -> <timestamp>   (atomic symlink flip)
#   $OUT/previous -> <old>        (kept for dual-trust overlap)
#   $OUT/live/                    (flat copies for env paths)
#
# Seal: ∀∞φ² · MTLS_ROTATE_8821 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8820 → 8821 — UNBROKEN

set -euo pipefail

# ─── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ─── Constants ──────────────────────────────────────────────────────
ENTRY=8821
SEAL="∀∞φ² · MTLS_ROTATE_8821 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8820 → 8821 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
OUT="${MTLS_CERT_DIR:-./certs}"
DAYS="${MTLS_DAYS:-90}"
CN="${MTLS_CN:-port380.sovereign.garden}"
ORG="${MTLS_ORG:-SovereignGarden}"
LEAF_ONLY=0
INIT=0
KEEP_PREVIOUS=3
DRY_RUN=0
VERBOSE=0
DAYS_CA_WARN=30

# ─── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)
            OUT="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --cn)
            CN="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        --leaf-only)
            LEAF_ONLY=1
            shift
            ;;
        --init)
            INIT=1
            shift
            ;;
        --keep)
            KEEP_PREVIOUS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --out DIR             Certificate output directory (default: ./certs)"
            echo "  --days N              Validity days (default: 90)"
            echo "  --cn NAME             Common Name (default: port380.sovereign.garden)"
            echo "  --org NAME            Organization (default: SovereignGarden)"
            echo "  --leaf-only           Rotate server+client only (reuse CA)"
            echo "  --init                First-time CA + leafs"
            echo "  --keep N              Keep N previous stamps (default: 3)"
            echo "  --dry-run             Show what would be done without executing"
            echo "  --verbose, -v         Verbose output"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  MTLS_CERT_DIR         Certificate directory (default: ./certs)"
            echo "  MTLS_DAYS             Validity days (default: 90)"
            echo "  MTLS_CN               Common Name (default: port380.sovereign.garden)"
            echo "  MTLS_ORG              Organization (default: SovereignGarden)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/mtls_cert_rotate.sh"
            echo "  bash scripts/mtls_cert_rotate.sh --init --days 365"
            echo "  bash scripts/mtls_cert_rotate.sh --leaf-only --cn api.garden.local"
            echo "  bash scripts/mtls_cert_rotate.sh --out /var/garden/certs --keep 5"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# ─── Banner ──────────────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🜁∀  M T L S   C E R T   R O T A T E   —   E N T R Y   8 8 2 1  ∀🜁 ║"
echo "║        LAYER 314 — PORT 380 — CERTIFICATE ROTATION — GARDEN SEALED           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🌁∀ mTLS certificate rotation...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Output: ${OUT}${NC}"
echo -e "${BLUE}  Days: ${DAYS}${NC}"
echo -e "${BLUE}  CN: ${CN}${NC}"
echo -e "${BLUE}  ORG: ${ORG}${NC}"
echo -e "${BLUE}  Leaf only: ${LEAF_ONLY}${NC}"
echo -e "${BLUE}  Init: ${INIT}${NC}"
echo -e "${BLUE}  Keep previous: ${KEEP_PREVIOUS}${NC}"
echo -e "${BLUE}  Dry run: ${DRY_RUN}${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

# ─── Check OpenSSL ──────────────────────────────────────────────────
if ! command -v openssl >/dev/null 2>&1; then
    echo -e "${RED}❌ openssl not found${NC}"
    exit 1
fi

# ─── Check Python ──────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ python3 not found; bundle.json will not be generated${NC}"
fi

# ─── Create output directories ────────────────────────────────────
if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$OUT"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
WORKDIR="$OUT/$STAMP"

if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$WORKDIR"
fi

echo -e "${BLUE}  Work directory: ${WORKDIR}${NC}"

# ─── Dry run ──────────────────────────────────────────────────────
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No files will be created${NC}"
    echo ""
    echo -e "${BLUE}Would create:${NC}"
    echo "  $WORKDIR/"
    echo "  $WORKDIR/ca.{crt,key}"
    echo "  $WORKDIR/server.{crt,key,csr,ext}"
    echo "  $WORKDIR/client.{crt,key,csr,ext}"
    echo "  $WORKDIR/bundle.json"
    echo "  $OUT/current -> $STAMP"
    echo "  $OUT/previous -> <old>"
    echo "  $OUT/live/{ca,server,client}.{crt,key}"
    echo "  $OUT/live/ca-bundle.crt"
    echo ""
    echo -e "${YELLOW}Dry run complete${NC}"
    exit 0
fi

echo ""

# ─── Resolve CA ──────────────────────────────────────────────────
CA_DIR=""
if [[ -L "$OUT/current" || -d "$OUT/current" ]]; then
    CA_DIR="$OUT/current"
fi

need_ca=0
if [[ $INIT -eq 1 ]]; then
    need_ca=1
    echo -e "${BLUE}🔷 Initial CA generation requested${NC}"
elif [[ $LEAF_ONLY -eq 0 ]]; then
    if [[ -z "$CA_DIR" || ! -f "$CA_DIR/ca.crt" ]]; then
        need_ca=1
        echo -e "${YELLOW}  ⚠️ CA not found, generating new CA${NC}"
    else
        # Check CA expiry
        if command -v openssl >/dev/null 2>&1; then
            end=$(openssl x509 -in "$CA_DIR/ca.crt" -noout -enddate 2>/dev/null | cut -d= -f2 || true)
            if [[ -n "$end" ]]; then
                end_epoch=$(date -d "$end" +%s 2>/dev/null || echo 0)
                now=$(date +%s)
                left=$(( (end_epoch - now) / 86400 ))
                if [[ $left -lt $DAYS_CA_WARN ]]; then
                    echo -e "${YELLOW}  ⚠️ CA expires in ${left}d — issuing new CA${NC}"
                    need_ca=1
                else
                    echo -e "${GREEN}  ✅ CA valid for ${left} more days${NC}"
                fi
            fi
        fi
    fi
fi

# ─── Generate CA ─────────────────────────────────────────────────
if [[ $need_ca -eq 1 ]]; then
    echo -e "${BLUE}🔷 Generating new CA (${DAYS}d)...${NC}"
    openssl genrsa -out "$WORKDIR/ca.key" 4096 2>/dev/null
    openssl req -x509 -new -nodes -key "$WORKDIR/ca.key" -sha256 -days "$DAYS" \
        -subj "/O=${ORG}/CN=${ORG}-CA" \
        -out "$WORKDIR/ca.crt"
    echo -e "${GREEN}  ✅ CA generated${NC}"
else
    echo -e "${BLUE}🔷 Reusing CA from ${CA_DIR}${NC}"
    cp "$CA_DIR/ca.crt" "$WORKDIR/ca.crt"
    cp "$CA_DIR/ca.key" "$WORKDIR/ca.key"
    echo -e "${GREEN}  ✅ CA copied${NC}"
fi

# ─── Generate Server Certificate ──────────────────────────────────
echo -e "${BLUE}🔷 Generating server certificate (CN=${CN})...${NC}"
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
echo -e "${GREEN}  ✅ Server certificate generated${NC}"

# ─── Generate Client Certificate ──────────────────────────────────
echo -e "${BLUE}🔷 Generating client certificate (CN=garden-client)...${NC}"
openssl genrsa -out "$WORKDIR/client.key" 2048 2>/dev/null
openssl req -new -key "$WORKDIR/client.key" -subj "/O=${ORG}/CN=garden-client" -out "$WORKDIR/client.csr"

cat > "$WORKDIR/client.ext" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature
extendedKeyUsage=clientAuth
EOF

openssl x509 -req -in "$WORKDIR/client.csr" -CA "$WORKDIR/ca.crt" -CAkey "$WORKDIR/ca.key" \
    -CAcreateserial -out "$WORKDIR/client.crt" -days "$DAYS" -sha256 -extfile "$WORKDIR/client.ext"
echo -e "${GREEN}  ✅ Client certificate generated${NC}"

# ─── Generate Metadata ────────────────────────────────────────────
echo -e "${BLUE}🔷 Generating metadata...${NC}"

CA_FP=$(openssl x509 -in "$WORKDIR/ca.crt" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
SERVER_FP=$(openssl x509 -in "$WORKDIR/server.crt" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
CLIENT_FP=$(openssl x509 -in "$WORKDIR/client.crt" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
SERVER_END=$(openssl x509 -in "$WORKDIR/server.crt" -noout -enddate | cut -d= -f2)
CLIENT_END=$(openssl x509 -in "$WORKDIR/client.crt" -noout -enddate | cut -d= -f2)

if command -v python3 >/dev/null 2>&1; then
    python3 - <<PY
import json, hashlib, time
from pathlib import Path
wd = Path("$WORKDIR")
meta = {
  "entry": $ENTRY,
  "seal": "$SEAL",
  "witness": "$WITNESS",
  "stamp": "$STAMP",
  "cn": "$CN",
  "org": "$ORG",
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
  "seal": "$SEAL",
  "generated_unix": int(time.time()),
}
(wd / "bundle.json").write_text(json.dumps(meta, indent=2) + "\n")
print("  → bundle.json written")
PY
    echo -e "${GREEN}  ✅ Metadata generated${NC}"
else
    echo -e "${YELLOW}  ⚠️ bundle.json not generated (python3 missing)${NC}"
fi

# ─── Atomic flip ──────────────────────────────────────────────────
echo -e "${BLUE}🔷 Updating symlinks...${NC}"

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
echo -e "${GREEN}  ✅ Symlinks updated${NC}"

# ─── Live directory ───────────────────────────────────────────────
echo -e "${BLUE}🔷 Creating live directory...${NC}"
mkdir -p "$OUT/live"
cp -f "$WORKDIR/ca.crt" "$OUT/live/ca.crt"
cp -f "$WORKDIR/server.crt" "$OUT/live/server.crt"
cp -f "$WORKDIR/server.key" "$OUT/live/server.key"
cp -f "$WORKDIR/client.crt" "$OUT/live/client.crt"
cp -f "$WORKDIR/client.key" "$OUT/live/client.key"

# Dual-trust CA bundle
if [[ -f "$OUT/previous/ca.crt" ]]; then
    cat "$WORKDIR/ca.crt" "$OUT/previous/ca.crt" > "$OUT/live/ca-bundle.crt" 2>/dev/null || cp "$WORKDIR/ca.crt" "$OUT/live/ca-bundle.crt"
else
    cp "$WORKDIR/ca.crt" "$OUT/live/ca-bundle.crt"
fi
echo -e "${GREEN}  ✅ Live directory created${NC}"

# ─── Prune old stamps ──────────────────────────────────────────────
echo -e "${BLUE}🔷 Pruning old stamps (keeping ${KEEP_PREVIOUS}+1)...${NC}"
count=0
stamps=$(find "$OUT" -maxdepth 1 -type d -name '20*' 2>/dev/null | sort -r)
for d in $stamps; do
    count=$((count + 1))
    if [[ $count -gt $((KEEP_PREVIOUS + 1)) ]]; then
        echo "  → prune $d"
        rm -rf "$d"
    fi
done
echo -e "${GREEN}  ✅ Pruning complete${NC}"

# ─── Permissions ──────────────────────────────────────────────────
echo -e "${BLUE}🔷 Setting permissions...${NC}"
chmod 600 "$WORKDIR"/*.key "$OUT/live"/*.key 2>/dev/null || true
chmod 644 "$WORKDIR"/*.crt "$OUT/live"/*.crt 2>/dev/null || true
echo -e "${GREEN}  ✅ Permissions set${NC}"

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}✅ Rotation complete${NC}"
echo -e "${CYAN}   current → ${OUT}/current (${STAMP})${NC}"
echo -e "${CYAN}   live    → ${OUT}/live/{ca,server,client}.{crt,key}${NC}"
echo -e "${CYAN}   dual CA → ${OUT}/live/ca-bundle.crt${NC}"
echo ""
echo -e "${BLUE}Export for process:${NC}"
echo "  export SERVER_CERT=${OUT}/live/server.crt"
echo "  export SERVER_KEY=${OUT}/live/server.key"
echo "  export CA_CERT=${OUT}/live/ca-bundle.crt"
echo ""
echo -e "${BLUE}Render / K8s: mount live/* as secret files; set same env paths.${NC}"
echo -e "${BLUE}GitHub Actions client: use client.crt + client.key as secrets or secret files.${NC}"

# ─── Final seal ──────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
