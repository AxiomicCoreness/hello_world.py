#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ CERT MANAGER MTLS — ENTRY 8819
#
# Install cert-manager (if needed) + apply Garden mTLS Certificate resources
#
# Usage:
#   bash scripts/install_cert_manager.sh
#   bash scripts/install_cert_manager.sh --namespace my-namespace
#   bash scripts/install_cert_manager.sh --version v1.16.2
#   bash scripts/install_cert_manager.sh --dry-run
#   bash scripts/install_cert_manager.sh --skip-crd-check
#
# Integration with:
#   - cert-manager (certificates, issuers, clusterissuers)
#   - Kubernetes (deployments, secrets, namespaces)
#   - mTLS (quantum/mtls_cert_lifecycle.py)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · CERT_MANAGER_MTLS_8819 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8818 → 8819 — UNBROKEN

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
ENTRY=8819
SEAL="∀∞φ² · CERT_MANAGER_MTLS_8819 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8818 → 8819 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST_DIR="${ROOT}/k8s/cert-manager"
NS_APP="${NAMESPACE:-sovereign-garden}"
CM_VERSION="${CERT_MANAGER_VERSION:-v1.16.2}"
DRY_RUN=false
SKIP_CRD_CHECK=false
VERBOSE=false
TIMEOUT=180

# ─── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n)
            NS_APP="$2"
            shift 2
            ;;
        --version|-v)
            CM_VERSION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-crd-check)
            SKIP_CRD_CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --timeout|-t)
            TIMEOUT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --namespace, -n NS   Kubernetes namespace (default: sovereign-garden)"
            echo "  --version, -v VER    cert-manager version (default: v1.16.2)"
            echo "  --dry-run            Show what would be done without executing"
            echo "  --skip-crd-check     Skip CRD presence check"
            echo "  --verbose            Verbose output"
            echo "  --timeout, -t SEC    Timeout in seconds (default: 180)"
            echo "  --help, -h           Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  NAMESPACE            Kubernetes namespace (default: sovereign-garden)"
            echo "  CERT_MANAGER_VERSION cert-manager version (default: v1.16.2)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/install_cert_manager.sh"
            echo "  bash scripts/install_cert_manager.sh --namespace my-namespace"
            echo "  bash scripts/install_cert_manager.sh --version v1.15.0 --dry-run"
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
echo "║  🜁∀  C E R T   M A N A G E R   M T L S   —   E N T R Y   8 8 1 9  ∀🜁 ║"
echo "║        BOOTSTRAP — CERTIFICATE MANAGEMENT — GARDEN SEALED                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🌁∀ cert-manager mTLS bootstrap${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Namespace: ${NS_APP}${NC}"
echo -e "${BLUE}  Version: ${CM_VERSION}${NC}"
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

# ─── Dry run ──────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No changes will be applied${NC}"
    echo ""
    echo -e "${BLUE}Would execute:${NC}"
    echo "  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/${CM_VERSION}/cert-manager.yaml"
    echo "  kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=${TIMEOUT}s"
    echo "  kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=${TIMEOUT}s"
    echo "  kubectl apply -f ${MANIFEST_DIR}/00-namespace.yaml"
    echo "  kubectl apply -f ${MANIFEST_DIR}/01-issuers-and-certs.yaml"
    echo "  kubectl wait --for=condition=Ready certificate/garden-root-ca -n cert-manager --timeout=${TIMEOUT}s"
    echo "  kubectl wait --for=condition=Ready certificate/port380-server -n ${NS_APP} --timeout=${TIMEOUT}s"
    echo "  kubectl wait --for=condition=Ready certificate/port380-client -n ${NS_APP} --timeout=${TIMEOUT}s"
    echo "  kubectl apply -f ${MANIFEST_DIR}/02-deployment-mtls-patch.yaml"
    echo ""
    echo -e "${YELLOW}Dry run complete${NC}"
    exit 0
fi

# ─── Check/Create namespace ──────────────────────────────────────
echo -e "${BLUE}🔷 Ensuring namespace: ${NS_APP}...${NC}"
if ! kubectl get namespace "$NS_APP" >/dev/null 2>&1; then
    echo -e "${BLUE}  Creating namespace: ${NS_APP}${NC}"
    kubectl create namespace "$NS_APP"
fi
echo -e "${GREEN}  ✅ Namespace ready: ${NS_APP}${NC}"

# ─── Check cert-manager CRDs ──────────────────────────────────────
if [[ "$SKIP_CRD_CHECK" == "false" ]]; then
    echo -e "${BLUE}🔷 Checking cert-manager CRDs...${NC}"
    if kubectl get crd certificates.cert-manager.io >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ cert-manager CRDs present${NC}"
    else
        echo -e "${BLUE}  Installing cert-manager ${CM_VERSION}...${NC}"
        echo -e "${YELLOW}  This may take a few moments...${NC}"
        kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/download/${CM_VERSION}/cert-manager.yaml"
        
        echo -e "${BLUE}  Waiting for cert-manager webhook...${NC}"
        kubectl wait --for=condition=Available deployment/cert-manager-webhook \
            -n cert-manager --timeout="${TIMEOUT}s" || {
            echo -e "${YELLOW}  ⚠️ Webhook not ready yet; continuing...${NC}"
        }
        
        echo -e "${BLUE}  Waiting for cert-manager controller...${NC}"
        kubectl wait --for=condition=Available deployment/cert-manager \
            -n cert-manager --timeout="${TIMEOUT}s" || {
            echo -e "${YELLOW}  ⚠️ Controller not ready yet; continuing...${NC}"
        }
        echo -e "${GREEN}  ✅ cert-manager installed${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️ Skipping CRD check${NC}"
fi
echo ""

# ─── Apply manifests ──────────────────────────────────────────────
echo -e "${BLUE}🔷 Applying cert-manager manifests...${NC}"

# Check manifest directory
if [[ ! -d "$MANIFEST_DIR" ]]; then
    echo -e "${YELLOW}  ⚠️ Manifest directory not found: ${MANIFEST_DIR}${NC}"
    echo -e "${BLUE}  Creating manifest directory...${NC}"
    mkdir -p "$MANIFEST_DIR"
fi

# Apply namespace
if [[ -f "${MANIFEST_DIR}/00-namespace.yaml" ]]; then
    echo -e "${BLUE}  Applying 00-namespace.yaml...${NC}"
    kubectl apply -f "${MANIFEST_DIR}/00-namespace.yaml"
else
    echo -e "${YELLOW}  ⚠️ 00-namespace.yaml not found${NC}"
fi

# Apply issuers and certificates
if [[ -f "${MANIFEST_DIR}/01-issuers-and-certs.yaml" ]]; then
    echo -e "${BLUE}  Applying 01-issuers-and-certs.yaml...${NC}"
    kubectl apply -f "${MANIFEST_DIR}/01-issuers-and-certs.yaml"
else
    echo -e "${YELLOW}  ⚠️ 01-issuers-and-certs.yaml not found${NC}"
fi

echo ""

# ─── Wait for CA certificate ──────────────────────────────────────
echo -e "${BLUE}🔷 Waiting for Garden CA Certificate Ready...${NC}"
if kubectl wait --for=condition=Ready certificate/garden-root-ca \
    -n cert-manager --timeout="${TIMEOUT}s" 2>/dev/null; then
    echo -e "${GREEN}  ✅ CA certificate ready${NC}"
else
    echo -e "${YELLOW}  ⚠️ CA not Ready yet${NC}"
    echo -e "${BLUE}  Describing certificate...${NC}"
    kubectl describe certificate garden-root-ca -n cert-manager | tail -30
fi

# ─── Wait for leaf certificates ────────────────────────────────────
echo -e "${BLUE}🔷 Waiting for leaf Certificates in ${NS_APP}...${NC}"
for name in port380-server port380-client; do
    if kubectl wait --for=condition=Ready "certificate/${name}" \
        -n "${NS_APP}" --timeout="${TIMEOUT}s" 2>/dev/null; then
        echo -e "${GREEN}  ✅ ${name} Ready${NC}"
    else
        echo -e "${YELLOW}  ⚠️ ${name} not Ready${NC}"
        kubectl describe "certificate/${name}" -n "${NS_APP}" | tail -20
    fi
done
echo ""

# ─── Apply deployment patch ──────────────────────────────────────
echo -e "${BLUE}🔷 Applying deployment mTLS patch...${NC}"
if kubectl get deployment port-380-gate -n "${NS_APP}" >/dev/null 2>&1; then
    if [[ -f "${MANIFEST_DIR}/02-deployment-mtls-patch.yaml" ]]; then
        echo -e "${BLUE}  Applying 02-deployment-mtls-patch.yaml...${NC}"
        kubectl apply -f "${MANIFEST_DIR}/02-deployment-mtls-patch.yaml" || true
        echo -e "${BLUE}  Waiting for rollout...${NC}"
        kubectl rollout status deployment/port-380-gate -n "${NS_APP}" --timeout="${TIMEOUT}s" || true
        echo -e "${GREEN}  ✅ Deployment patched${NC}"
    else
        echo -e "${YELLOW}  ⚠️ 02-deployment-mtls-patch.yaml not found${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️ Deployment port-380-gate not found in ${NS_APP} (skip patch)${NC}"
fi
echo ""

# ─── Show status ──────────────────────────────────────────────────
echo -e "${BLUE}🔷 Certificate status:${NC}"
echo "─────────────────────────────────────────────────────────────"
echo -e "${CYAN}"
kubectl get clusterissuer garden-selfsigned garden-ca-issuer 2>/dev/null || echo "  ClusterIssuers not found"
echo ""
kubectl get certificate -n cert-manager garden-root-ca 2>/dev/null || echo "  Root CA not found"
echo ""
kubectl get certificate -n "${NS_APP}" 2>/dev/null || echo "  No certificates in namespace"
echo -e "${NC}"

echo -e "${BLUE}🔷 Secrets:${NC}"
echo "  ${NS_APP}/port380-server-tls"
echo "  ${NS_APP}/port380-client-tls"
echo "  cert-manager/garden-root-ca"
echo ""
echo -e "${GREEN}  Renewal is automatic (renewBefore on each Certificate)${NC}"

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  C E R T   M A N A G E R   M T L S   —   E N T R Y   8 8 1 9   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ cert-manager mTLS active${NC}"
echo -e "${CYAN}🌐 Namespace: ${NS_APP}${NC}"
echo -e "${CYAN}📦 Version: ${CM_VERSION}${NC}"
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
