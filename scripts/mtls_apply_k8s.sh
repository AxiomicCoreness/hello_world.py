#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ MTLS APPLY KUBERNETES — ENTRY 8820
#
# Apply rotated mTLS material to Kubernetes secret in namespace sovereign-garden (or $NS).
# Prerequisites: kubectl context; certs/live populated by mtls_cert_rotate.sh
#
# Usage:
#   bash scripts/mtls_apply_kubernetes.sh
#   bash scripts/mtls_apply_kubernetes.sh --namespace my-namespace
#   bash scripts/mtls_apply_kubernetes.sh --cert-dir ./certs
#   bash scripts/mtls_apply_kubernetes.sh --secret-name port380-mtls
#   bash scripts/mtls_apply_kubernetes.sh --dry-run
#
# Integration with:
#   - Kubernetes (secrets, deployments)
#   - mTLS (quantum/mtls_cert_lifecycle.py)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · MTLS_ROTATE_8820 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8819 → 8820 — UNBROKEN

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
ENTRY=8820
SEAL="∀∞φ² · MTLS_ROTATE_8820 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8819 → 8820 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NS="${NAMESPACE:-sovereign-garden}"
CERT_DIR="${MTLS_CERT_DIR:-./certs}"
SECRET_NAME="${MTLS_SECRET_NAME:-port380-mtls}"
LIVE="$CERT_DIR/live"
DRY_RUN=false
VERBOSE=false
RESTART_DEPLOYMENT=true
FORCE=false
BACKUP_SECRET=false

# ─── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n)
            NS="$2"
            shift 2
            ;;
        --cert-dir|-c)
            CERT_DIR="$2"
            LIVE="$CERT_DIR/live"
            shift 2
            ;;
        --secret-name|-s)
            SECRET_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --no-restart)
            RESTART_DEPLOYMENT=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --backup)
            BACKUP_SECRET=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --namespace, -n NS        Kubernetes namespace (default: sovereign-garden)"
            echo "  --cert-dir, -c DIR        Certificate directory (default: ./certs)"
            echo "  --secret-name, -s NAME    Secret name (default: port380-mtls)"
            echo "  --dry-run                 Show what would be done without executing"
            echo "  --verbose, -v             Verbose output"
            echo "  --no-restart              Skip deployment restart"
            echo "  --force                   Force apply even if certs are missing"
            echo "  --backup                  Backup existing secret before applying"
            echo "  --help, -h                Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  NAMESPACE                 Kubernetes namespace (default: sovereign-garden)"
            echo "  MTLS_CERT_DIR             Certificate directory (default: ./certs)"
            echo "  MTLS_SECRET_NAME          Secret name (default: port380-mtls)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/mtls_apply_kubernetes.sh"
            echo "  bash scripts/mtls_apply_kubernetes.sh --namespace my-namespace --dry-run"
            echo "  bash scripts/mtls_apply_kubernetes.sh --cert-dir ./certs --secret-name my-secret"
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
echo "║  🜁∀  M T L S   A P P L Y   K U B E R N E T E S   —   E N T R Y   8 8 2 0  ∀🜁 ║"
echo "║        ROTATE CERTIFICATES — KUBERNETES SECRETS — GARDEN SEALED              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🌁∀ Applying mTLS material to Kubernetes...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Namespace: ${NS}${NC}"
echo -e "${BLUE}  Cert Dir: ${CERT_DIR}${NC}"
echo -e "${BLUE}  Live Dir: ${LIVE}${NC}"
echo -e "${BLUE}  Secret: ${SECRET_NAME}${NC}"
echo -e "${BLUE}  Dry run: ${DRY_RUN}${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

# ─── Check kubectl ─────────────────────────────────────────────────
if ! command -v kubectl >/dev/null 2>&1; then
    echo -e "${RED}❌ kubectl not found${NC}"
    exit 1
fi

# ─── Check cluster connectivity ────────────────────────────────────
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Cluster connected${NC}"

# ─── Check certificate files ──────────────────────────────────────
echo -e "${BLUE}🔷 Checking certificate files...${NC}"

if [[ ! -d "$LIVE" ]]; then
    echo -e "${YELLOW}  ⚠️ Live directory not found: ${LIVE}${NC}"
    if [[ "$FORCE" == "true" ]]; then
        echo -e "${YELLOW}  Force mode: continuing${NC}"
    else
        echo -e "${RED}  ❌ Run: bash scripts/mtls_cert_rotate.sh first${NC}"
        exit 1
    fi
fi

MISSING_FILES=()
for file in server.crt server.key; do
    if [[ ! -f "$LIVE/$file" ]]; then
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo -e "${YELLOW}  ⚠️ Missing files: ${MISSING_FILES[*]}${NC}"
    if [[ "$FORCE" == "true" ]]; then
        echo -e "${YELLOW}  Force mode: continuing${NC}"
    else
        echo -e "${RED}  ❌ Missing certificate files${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✅ Certificate files present${NC}"
fi

# Determine CA file
CA_FILE="$LIVE/ca-bundle.crt"
if [[ ! -f "$CA_FILE" ]]; then
    CA_FILE="$LIVE/ca.crt"
fi

if [[ ! -f "$CA_FILE" ]]; then
    echo -e "${YELLOW}  ⚠️ CA file not found: ${CA_FILE}${NC}"
    CA_FILE=""
fi

# Check client certs
CLIENT_CRT="$LIVE/client.crt"
CLIENT_KEY="$LIVE/client.key"
HAS_CLIENT=false
if [[ -f "$CLIENT_CRT" && -f "$CLIENT_KEY" ]]; then
    HAS_CLIENT=true
    echo -e "${GREEN}  ✅ Client certificates present${NC}"
fi

echo ""

# ─── Dry run ──────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No changes will be applied${NC}"
    echo ""
    echo -e "${BLUE}Would execute:${NC}"
    echo "  kubectl create secret generic $SECRET_NAME \\"
    echo "    --namespace=$NS \\"
    echo "    --from-file=server.crt=$LIVE/server.crt \\"
    echo "    --from-file=server.key=$LIVE/server.key \\"
    if [[ -n "$CA_FILE" ]]; then
        echo "    --from-file=ca.crt=$CA_FILE \\"
    fi
    if [[ "$HAS_CLIENT" == "true" ]]; then
        echo "    --from-file=client.crt=$CLIENT_CRT \\"
        echo "    --from-file=client.key=$CLIENT_KEY \\"
    fi
    echo "    --dry-run=client -o yaml | kubectl apply -f -"
    echo ""
    echo "  kubectl annotate secret $SECRET_NAME -n $NS \\"
    echo "    garden.sovereign/mtls-rotated-at=\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" \\"
    echo "    garden.sovereign/seal=\"MTLS_ROTATE\" \\"
    echo "    --overwrite"
    echo ""
    if [[ "$RESTART_DEPLOYMENT" == "true" ]]; then
        echo "  kubectl rollout restart deployment/port-380-gate -n $NS"
    fi
    echo ""
    echo -e "${YELLOW}Dry run complete${NC}"
    exit 0
fi

# ─── Backup existing secret ──────────────────────────────────────
if [[ "$BACKUP_SECRET" == "true" ]]; then
    echo -e "${BLUE}🔷 Backing up existing secret...${NC}"
    BACKUP_NAME="${SECRET_NAME}-backup-$(date +%s)"
    if kubectl get secret "$SECRET_NAME" -n "$NS" >/dev/null 2>&1; then
        kubectl get secret "$SECRET_NAME" -n "$NS" -o yaml > "/tmp/${BACKUP_NAME}.yaml"
        echo -e "${GREEN}  ✅ Backup saved: /tmp/${BACKUP_NAME}.yaml${NC}"
    else
        echo -e "${YELLOW}  ⚠️ Secret does not exist (no backup)${NC}"
    fi
fi

# ─── Build secret command ──────────────────────────────────────────
echo -e "${BLUE}🔷 Creating/updating secret: ${SECRET_NAME}...${NC}"

SECRET_CMD=("kubectl" "create" "secret" "generic" "$SECRET_NAME")
SECRET_CMD+=("--namespace=$NS")
SECRET_CMD+=("--from-file=server.crt=$LIVE/server.crt")
SECRET_CMD+=("--from-file=server.key=$LIVE/server.key")

if [[ -n "$CA_FILE" ]]; then
    SECRET_CMD+=("--from-file=ca.crt=$CA_FILE")
fi

if [[ "$HAS_CLIENT" == "true" ]]; then
    SECRET_CMD+=("--from-file=client.crt=$CLIENT_CRT")
    SECRET_CMD+=("--from-file=client.key=$CLIENT_KEY")
fi

SECRET_CMD+=("--dry-run=client" "-o" "yaml")

if [[ "$VERBOSE" == "true" ]]; then
    echo -e "${CYAN}Command: ${SECRET_CMD[*]}${NC}"
    echo ""
fi

# Apply secret
if "${SECRET_CMD[@]}" | kubectl apply -f -; then
    echo -e "${GREEN}  ✅ Secret applied: ${SECRET_NAME}${NC}"
else
    echo -e "${RED}  ❌ Failed to apply secret${NC}"
    exit 1
fi

# ─── Annotate secret ──────────────────────────────────────────────
echo -e "${BLUE}🔷 Annotating secret...${NC}"
if kubectl annotate secret "$SECRET_NAME" -n "$NS" \
    "garden.sovereign/mtls-rotated-at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "garden.sovereign/seal=MTLS_ROTATE_${ENTRY}" \
    "garden.sovereign/entry=${ENTRY}" \
    --overwrite; then
    echo -e "${GREEN}  ✅ Secret annotated${NC}"
else
    echo -e "${YELLOW}  ⚠️ Failed to annotate secret${NC}"
fi

# ─── Restart deployment ──────────────────────────────────────────
if [[ "$RESTART_DEPLOYMENT" == "true" ]]; then
    echo -e "${BLUE}🔷 Checking for deployment...${NC}"
    if kubectl get deployment port-380-gate -n "$NS" >/dev/null 2>&1; then
        echo -e "${BLUE}  Restarting deployment: port-380-gate${NC}"
        kubectl rollout restart deployment/port-380-gate -n "$NS"
        echo -e "${BLUE}  Waiting for rollout...${NC}"
        if kubectl rollout status deployment/port-380-gate -n "$NS" --timeout=120s 2>/dev/null; then
            echo -e "${GREEN}  ✅ Rollout complete${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Rollout timeout or failure${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️ Deployment not found: port-380-gate${NC}"
    fi
fi

# ─── Show status ──────────────────────────────────────────────────
echo ""
echo -e "${BLUE}🔷 Secret status:${NC}"
echo "─────────────────────────────────────────────────────────────"
kubectl get secret "$SECRET_NAME" -n "$NS" -o json | jq -r '.metadata | {name: .name, namespace: .namespace, annotations: .annotations}' 2>/dev/null || \
kubectl describe secret "$SECRET_NAME" -n "$NS" | head -10

echo ""
echo -e "${GREEN}✅ K8s mTLS secret applied. Mount paths should match:${NC}"
echo "   SERVER_CERT=/certs/server.crt"
echo "   SERVER_KEY=/certs/server.key"
echo "   CA_CERT=/certs/ca.crt"

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  M T L S   A P P L Y   K U B E R N E T E S   —   E N T R Y   8 8 2 0   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ mTLS secret applied${NC}"
echo -e "${CYAN}🌐 Namespace: ${NS}${NC}"
echo -e "${CYAN}🔑 Secret: ${SECRET_NAME}${NC}"
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
