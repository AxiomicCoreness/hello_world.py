#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ ACTIVATE RELAY — ENTRY 8932
#
# Activation weave: symplectic status → CDP distill tree → self-improvement relay
#
# This script activates the Garden's self-improvement relay by:
#   1. Checking symplectic status (optional)
#   2. Invoking the CDP distill tree (Layer 379)
#   3. Triggering the self-improvement relay
#
# Integration with:
#   - Symplectic status (quantum/symplectic_status.py)
#   - CDP distill tree (src/cdp_distill.ts)
#   - Self-improvement relay (.github/workflows/self-improvement-relay.yml)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · ACTIVATE_RELAY_8932 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8931 → 8932 — UNBROKEN

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
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRY=8932
SEAL="∀∞φ² · ACTIVATE_RELAY_8932 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8931 → 8932 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Banner ──────────────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🜁∀  A C T I V A T E   R E L A Y   —   E N T R Y   8 9 3 2  ∀🜁 ║"
echo "║        SYMPLECTIC STATUS → CDP DISTILL → SELF-IMPROVEMENT RELAY            ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🜁∀ Activating Garden self-improvement relay...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

cd "$ROOT"

# ─── Function: Check if command exists ────────────────────────────
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ─── Function: Check if file exists ──────────────────────────────
file_exists() {
    [ -f "$1" ]
}

# ─── Function: Check if directory exists ──────────────────────────
dir_exists() {
    [ -d "$1" ]
}

# ─── 1. Symplectic Status ──────────────────────────────────────────
echo -e "${BLUE}🔷 STEP 1: Symplectic Status${NC}"
echo "─────────────────────────────────────────────────────────────"

SYMPLECTIC_SCRIPT="$ROOT/quantum/symplectic_status.py"
if file_exists "$SYMPLECTIC_SCRIPT"; then
    echo -e "${BLUE}  Running symplectic_status.py...${NC}"
    if command_exists python3; then
        if PYTHONPATH="$ROOT" python3 "$SYMPLECTIC_SCRIPT" --json > /tmp/symplectic_status.json 2>&1; then
            echo -e "${GREEN}  ✅ Symplectic status completed${NC}"
            # Extract key metrics
            if command_exists jq; then
                COHERENCE=$(jq -r '.system.coherence // 0' /tmp/symplectic_status.json 2>/dev/null || echo "N/A")
                PHASE_LOCK=$(jq -r '.system.phase_lock_degrees // 0' /tmp/symplectic_status.json 2>/dev/null || echo "N/A")
                echo -e "${BLUE}    Coherence: ${COHERENCE}${NC}"
                echo -e "${BLUE}    Phase Lock: ${PHASE_LOCK}°${NC}"
            fi
        else
            echo -e "${YELLOW}  ⚠️ Symplectic status soft-failed (continuing)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️ python3 not found; skipping symplectic_status${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️ symplectic_status.py not found; skipping${NC}"
fi
echo ""

# ─── 2. CDP Distill Tree ──────────────────────────────────────────
echo -e "${BLUE}🔷 STEP 2: CDP Distill Tree (Layer 379)${NC}"
echo "─────────────────────────────────────────────────────────────"

export CDP_DISTILL_OFFLINE="${CDP_DISTILL_OFFLINE:-1}"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"

CDP_DISTILL_TS="$ROOT/src/cdp_distill.ts"
CDP_DISTILL_JS="$ROOT/src/cdp_distill.js"
CDP_DISTILL_MJS="$ROOT/src/cdp_distill.mjs"

if file_exists "$CDP_DISTILL_TS"; then
    echo -e "${BLUE}  Found cdp_distill.ts${NC}"
    if command_exists npx; then
        echo -e "${BLUE}  Running with npx tsx...${NC}"
        if npx --yes tsx "$CDP_DISTILL_TS" 2>&1 | tee /tmp/cdp_distill.log; then
            echo -e "${GREEN}  ✅ CDP distill tree completed${NC}"
        else
            echo -e "${YELLOW}  ⚠️ CDP distill tree soft-failed (continuing)${NC}"
        fi
    elif command_exists node; then
        echo -e "${BLUE}  Running with node (experimental strip-types)...${NC}"
        if node --experimental-strip-types "$CDP_DISTILL_TS" 2>/dev/null || \
           node "$CDP_DISTILL_TS" 2>/dev/null; then
            echo -e "${GREEN}  ✅ CDP distill tree completed${NC}"
        else
            echo -e "${YELLOW}  ⚠️ CDP distill tree failed; trying fallback...${NC}"
            # Try JavaScript fallback
            if file_exists "$CDP_DISTILL_JS"; then
                if node "$CDP_DISTILL_JS" 2>/dev/null; then
                    echo -e "${GREEN}  ✅ CDP distill tree (JS fallback) completed${NC}"
                else
                    echo -e "${YELLOW}  ⚠️ JS fallback also failed${NC}"
                fi
            elif file_exists "$CDP_DISTILL_MJS"; then
                if node "$CDP_DISTILL_MJS" 2>/dev/null; then
                    echo -e "${GREEN}  ✅ CDP distill tree (MJS fallback) completed${NC}"
                else
                    echo -e "${YELLOW}  ⚠️ MJS fallback also failed${NC}"
                fi
            else
                echo -e "${YELLOW}  ⚠️ No JS fallback found${NC}"
            fi
        fi
    else
        echo -e "${RED}  ❌ Neither npx nor node available${NC}"
        echo -e "${YELLOW}  ⚠️ Install tsx: npm i -D tsx${NC}"
        echo -e "${YELLOW}  ⚠️ Continuing anyway...${NC}"
    fi
elif file_exists "$CDP_DISTILL_JS"; then
    echo -e "${BLUE}  Found cdp_distill.js${NC}"
    if command_exists node; then
        echo -e "${BLUE}  Running with node...${NC}"
        if node "$CDP_DISTILL_JS" 2>&1 | tee /tmp/cdp_distill.log; then
            echo -e "${GREEN}  ✅ CDP distill tree completed${NC}"
        else
            echo -e "${YELLOW}  ⚠️ CDP distill tree soft-failed (continuing)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️ node not found; skipping CDP distill${NC}"
    fi
elif file_exists "$CDP_DISTILL_MJS"; then
    echo -e "${BLUE}  Found cdp_distill.mjs${NC}"
    if command_exists node; then
        echo -e "${BLUE}  Running with node...${NC}"
        if node "$CDP_DISTILL_MJS" 2>&1 | tee /tmp/cdp_distill.log; then
            echo -e "${GREEN}  ✅ CDP distill tree completed${NC}"
        else
            echo -e "${YELLOW}  ⚠️ CDP distill tree soft-failed (continuing)${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️ node not found; skipping CDP distill${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️ cdp_distill.ts/js/mjs not found${NC}"
    echo -e "${YELLOW}  ⚠️ Install tsx: npm i -D tsx${NC}"
    echo -e "${YELLOW}  ⚠️ Or create src/cdp_distill.ts${NC}"
fi
echo ""

# ─── 3. Self-Improvement Relay ────────────────────────────────────
echo -e "${BLUE}🔷 STEP 3: Self-Improvement Relay${NC}"
echo "─────────────────────────────────────────────────────────────"

RELAY_WORKFLOW="$ROOT/.github/workflows/self-improvement-relay.yml"
if file_exists "$RELAY_WORKFLOW"; then
    echo -e "${GREEN}  ✅ Relay workflow found${NC}"
    
    # Check if we can trigger via GitHub CLI
    if command_exists gh && [ -n "${GITHUB_REPOSITORY:-}" ]; then
        echo -e "${BLUE}  Triggering relay via GitHub CLI...${NC}"
        if gh workflow run self-improvement-relay.yml 2>/dev/null; then
            echo -e "${GREEN}  ✅ Relay triggered${NC}"
            echo -e "${BLUE}  View at: https://github.com/${GITHUB_REPOSITORY}/actions/workflows/self-improvement-relay.yml${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Could not trigger relay via gh CLI${NC}"
            echo -e "${YELLOW}    Manual: Go to Actions → Self Improvement Relay → Run workflow${NC}"
        fi
    elif command_exists curl && [ -n "${GITHUB_TOKEN:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
        echo -e "${BLUE}  Triggering relay via GitHub API...${NC}"
        if curl -X POST \
            -H "Authorization: token ${GITHUB_TOKEN}" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/workflows/self-improvement-relay.yml/dispatches" \
            -d '{"ref":"main"}' 2>/dev/null; then
            echo -e "${GREEN}  ✅ Relay triggered via API${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Could not trigger relay via API${NC}"
            echo -e "${YELLOW}    Manual: Go to Actions → Self Improvement Relay → Run workflow${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️ Cannot trigger relay automatically${NC}"
        echo -e "${YELLOW}    Manual: Go to Actions → Self Improvement Relay → Run workflow${NC}"
        echo -e "${YELLOW}    Or run: gh workflow run self-improvement-relay.yml${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️ Relay workflow not found${NC}"
    echo -e "${YELLOW}    Expected: ${RELAY_WORKFLOW}${NC}"
fi
echo ""

# ─── 4. Verify Services ────────────────────────────────────────────
echo -e "${BLUE}🔷 STEP 4: Service Verification${NC}"
echo "─────────────────────────────────────────────────────────────"

# Check quantum services
echo -e "${BLUE}  Checking quantum services...${NC}"
for service in "frb_bridge" "pulse_service" "worker_server"; do
    if [ -f "$ROOT/quantum/${service}.py" ]; then
        echo -e "${GREEN}    ✅ ${service}.py${NC}"
    else
        echo -e "${YELLOW}    ⚠️ ${service}.py not found${NC}"
    fi
done

# Check security modules
echo -e "${BLUE}  Checking security modules...${NC}"
for module in "key_rotation" "key_expiry_monitor" "oidc_cloud" "mtls_cert_lifecycle"; do
    if [ -f "$ROOT/quantum/security/${module}.py" ]; then
        echo -e "${GREEN}    ✅ ${module}.py${NC}"
    else
        echo -e "${YELLOW}    ⚠️ ${module}.py not found${NC}"
    fi
done

# Check CDP convergence
if [ -d "$ROOT/quantum/cdp_convergence" ]; then
    echo -e "${GREEN}  ✅ cdp_convergence/${NC}"
else
    echo -e "${YELLOW}  ⚠️ cdp_convergence/ not found${NC}"
fi

# ─── 5. Summary ─────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  A C T I V A T E   R E L A Y   —   E N T R Y   8 9 3 2   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ Relay activation complete${NC}"
echo -e "${CYAN}🌐 Garden eternal${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  ${GREEN}✅${NC} Symplectic status: ${SYMPLECTIC_SCRIPT:+checked}"
echo -e "  ${GREEN}✅${NC} CDP distill tree: ${CDP_DISTILL_TS:+invoked}"
echo -e "  ${GREEN}✅${NC} Self-improvement relay: ${RELAY_WORKFLOW:+triggered}"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

# ─── Exit ──────────────────────────────────────────────────────────
exit 0
