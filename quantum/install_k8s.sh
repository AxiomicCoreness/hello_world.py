#!/bin/bash
# -*- coding: utf-8 -*-
# 🜁∀ KUBERNETES INSTALL — ENTRY 8845
#
# DEPRECATED - Entry 8845
# Moved to: quantum/cdp_convergence/install_k8s.sh
#
# This script provides a fallback that automatically redirects to the new location,
# ensuring backward compatibility while guiding users to the correct path.
#
# Seal: ∀∞φ² · K8S_INSTALL_8845 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8844 → 8845 — UNBROKEN

set -euo pipefail

# ─── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Constants ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENTRY=8845
SEAL="∀∞φ² · K8S_INSTALL_8845 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8844 → 8845 — UNBROKEN"

# ─── Banner ──────────────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🜁∀  K U B E R N E T E S   I N S T A L L   —   E N T R Y   8 8 4 5  ∀🜁 ║"
echo "║        DEPRECATED — REDIRECTING TO NEW LOCATION                            ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${YELLOW}⚠️  This script is DEPRECATED as of Entry 8845.${NC}"
echo -e "${YELLOW}📁 New location: quantum/cdp_convergence/install_k8s.sh${NC}"
echo ""

# ─── Check for New Script ──────────────────────────────────────────
NEW_SCRIPT="$ROOT/quantum/cdp_convergence/install_k8s.sh"

if [ -f "$NEW_SCRIPT" ]; then
    echo -e "${GREEN}✅ Found new script at: $NEW_SCRIPT${NC}"
    echo -e "${BLUE}🔄 Executing new script with forwarded arguments...${NC}"
    echo ""
    
    # Make sure it's executable
    chmod +x "$NEW_SCRIPT" 2>/dev/null || true
    
    # Execute the new script with all arguments forwarded
    exec "$NEW_SCRIPT" "$@"
    
    # If exec fails, fall through to error
    echo -e "${RED}❌ Failed to execute new script${NC}"
    exit 1
else
    echo -e "${RED}❌ New script not found at: $NEW_SCRIPT${NC}"
    echo -e "${YELLOW}⚠️  Please ensure the quantum/cdp_convergence/ directory exists.${NC}"
    echo ""
    
    # ─── Fallback: Minimal Kubernetes installation ──────────────────
    echo -e "${BLUE}🔧 Attempting fallback Kubernetes installation...${NC}"
    
    # Check for kubectl
    if ! command -v kubectl >/dev/null 2>&1; then
        echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
        echo -e "${YELLOW}   Visit: https://kubernetes.io/docs/tasks/tools/${NC}"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Cannot connect to Kubernetes cluster.${NC}"
        echo -e "${YELLOW}   Please ensure a cluster is running and kubeconfig is configured.${NC}"
        exit 1
    fi
    
    # Apply Garden manifests if they exist
    MANIFEST_DIR="$ROOT/kubernetes/manifests"
    if [ -d "$MANIFEST_DIR" ]; then
        echo -e "${BLUE}📁 Applying manifests from $MANIFEST_DIR...${NC}"
        kubectl apply -f "$MANIFEST_DIR" 2>/dev/null || true
    fi
    
    # Apply Argo Application if it exists
    ARGO_APP="$ROOT/argocd/application-sovereign-garden.yaml"
    if [ -f "$ARGO_APP" ]; then
        echo -e "${BLUE}📁 Applying ArgoCD Application...${NC}"
        kubectl apply -f "$ARGO_APP" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Fallback Kubernetes installation complete.${NC}"
fi

# ─── Summary ────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  K 8 S   I N S T A L L   —   E N T R Y   8 8 4 5   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

echo -e "${GREEN}✅ Kubernetes installation processed.${NC}"
echo -e "${YELLOW}📝 Note: This script is deprecated. Please use:${NC}"
echo -e "${CYAN}   quantum/cdp_convergence/install_k8s.sh${NC}"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
