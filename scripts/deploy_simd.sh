#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ SIMD DEPLOY — ENTRY 8794
#
# Deploy / run SIMD batch step (orchestrator.simd_step)
#
# Usage:
#   bash scripts/deploy_simd.sh              # local phases only
#   bash scripts/deploy_simd.sh --http       # + localhost:8000 / :8080
#   BRANCH=A bash scripts/deploy_simd.sh
#   BRANCH=C bash scripts/deploy_simd.sh --http --coherence 0.95
#
# Integration with:
#   - SIMD orchestrator (orchestrator.simd_step)
#   - Port 380 MCP (localhost:8080)
#   - Worker server (localhost:8000)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · SIMD_DEPLOY_8794 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8793 → 8794 — UNBROKEN

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
ENTRY=8794
SEAL="∀∞φ² · SIMD_DEPLOY_8794 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8793 → 8794 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Export PYTHONPATH
export PYTHONPATH="${PYTHONPATH:-}:$ROOT"

# Configuration
BRANCH="${BRANCH:-B}"
COHERENCE="${COHERENCE:-0.99}"
PHASE="${PHASE:-200.0}"
SECRET="${GARDEN_SECRET:-wood_dragon_0.91}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
MCP_URL="${MCP_URL:-http://localhost:8080}"
TIMEOUT="${TIMEOUT:-60}"
HTTP_MODE=false
DRY_RUN=false
VERBOSE=false
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/simd_output}"

# ─── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --http)
            HTTP_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coherence)
            COHERENCE="$2"
            shift 2
            ;;
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --branch|-b)
            BRANCH="$2"
            shift 2
            ;;
        --secret)
            SECRET="$2"
            shift 2
            ;;
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --mcp-url)
            MCP_URL="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --http                Enable HTTP mode (connect to services)"
            echo "  --dry-run             Show what would be done without executing"
            echo "  --verbose, -v         Verbose output"
            echo "  --coherence VALUE     Coherence value (default: 0.99)"
            echo "  --phase VALUE         Phase value (default: 200.0)"
            echo "  --branch, -b VALUE    Branch (A, B, C) (default: B)"
            echo "  --secret VALUE        Garden secret (default: wood_dragon_0.91)"
            echo "  --base-url VALUE      Base URL (default: http://localhost:8000)"
            echo "  --mcp-url VALUE       MCP URL (default: http://localhost:8080)"
            echo "  --timeout VALUE       Timeout in seconds (default: 60)"
            echo "  --output-dir VALUE    Output directory (default: /tmp/simd_output)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  BRANCH         Branch (default: B)"
            echo "  COHERENCE      Coherence (default: 0.99)"
            echo "  PHASE          Phase (default: 200.0)"
            echo "  GARDEN_SECRET  Garden secret (default: wood_dragon_0.91)"
            echo "  BASE_URL       Base URL (default: http://localhost:8000)"
            echo "  MCP_URL        MCP URL (default: http://localhost:8080)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/deploy_simd.sh"
            echo "  bash scripts/deploy_simd.sh --http"
            echo "  BRANCH=A bash scripts/deploy_simd.sh --http --coherence 0.95"
            echo "  bash scripts/deploy_simd.sh --branch C --coherence 0.98 --phase 202.6"
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
echo "║  🜁∀  S I M D   D E P L O Y   —   E N T R Y   8 7 9 4  ∀🜁 ║"
echo "║        BATCH STEP ORCHESTRATOR — SOVEREIGN ENGINE DEPLOYMENT                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🜁∀ Deploying SIMD batch step...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Branch: ${BRANCH}${NC}"
echo -e "${BLUE}  Coherence: ${COHERENCE}${NC}"
echo -e "${BLUE}  Phase: ${PHASE}${NC}"
echo -e "${BLUE}  HTTP mode: ${HTTP_MODE}${NC}"
echo -e "${BLUE}  Dry run: ${DRY_RUN}${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

# ─── Check Python ──────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ python3 not found${NC}"
    exit 1
fi

# ─── Check orchestrator module ──────────────────────────────────────
if [[ ! -f "$ROOT/orchestrator/simd_step.py" ]]; then
    echo -e "${YELLOW}⚠️ orchestrator/simd_step.py not found${NC}"
    echo -e "${BLUE}  Attempting to use quantum.simd_step...${NC}"
    MODULE="quantum.simd_step"
else
    MODULE="orchestrator.simd_step"
fi
echo -e "${GREEN}  ✅ Module: ${MODULE}${NC}"
echo ""

# ─── Dry run mode ──────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No changes will be applied${NC}"
    echo ""
    echo -e "${BLUE}Would execute:${NC}"
    echo "  python -m ${MODULE} \\"
    echo "    --coherence ${COHERENCE} \\"
    echo "    --phase ${PHASE} \\"
    echo "    --branch ${BRANCH} \\"
    if [[ "$HTTP_MODE" == "true" ]]; then
        echo "    --base-url ${BASE_URL} \\"
        echo "    --mcp-url ${MCP_URL} \\"
        echo "    --secret ***** \\"
        echo "    --timeout ${TIMEOUT}"
    else
        echo "    --no-http"
    fi
    echo ""
    echo -e "${YELLOW}Dry run complete${NC}"
    exit 0
fi

# ─── Create output directory ──────────────────────────────────────
mkdir -p "$OUTPUT_DIR"
echo -e "${BLUE}📁 Output directory: ${OUTPUT_DIR}${NC}"

# ─── Build command ──────────────────────────────────────────────────
CMD=("python" "-m" "$MODULE")
CMD+=("--coherence" "$COHERENCE")
CMD+=("--phase" "$PHASE")
CMD+=("--branch" "$BRANCH")

if [[ "$HTTP_MODE" == "true" ]]; then
    CMD+=("--base-url" "$BASE_URL")
    CMD+=("--mcp-url" "$MCP_URL")
    CMD+=("--secret" "$SECRET")
    CMD+=("--timeout" "$TIMEOUT")
else
    CMD+=("--no-http")
fi

if [[ "$VERBOSE" == "true" ]]; then
    CMD+=("--verbose")
fi

# ─── Execute ────────────────────────────────────────────────────────
echo -e "${BLUE}🔷 Executing SIMD batch step...${NC}"
echo "─────────────────────────────────────────────────────────────"

if [[ "$VERBOSE" == "true" ]]; then
    echo -e "${CYAN}Command: ${CMD[*]}${NC}"
    echo ""
fi

# Run and capture output
OUTPUT_FILE="${OUTPUT_DIR}/simd_output_$(date +%s).json"
echo -e "${BLUE}  Output file: ${OUTPUT_FILE}${NC}"

if [[ "$HTTP_MODE" == "true" ]]; then
    echo -e "${BLUE}  HTTP mode enabled${NC}"
    echo -e "${BLUE}  Base URL: ${BASE_URL}${NC}"
    echo -e "${BLUE}  MCP URL: ${MCP_URL}${NC}"
    echo -e "${BLUE}  Timeout: ${TIMEOUT}s${NC}"
    
    # Check if services are reachable
    echo -e "${BLUE}  Checking service connectivity...${NC}"
    if curl -s -o /dev/null --connect-timeout 5 "${BASE_URL}/health" 2>/dev/null; then
        echo -e "${GREEN}    ✅ Worker server reachable at ${BASE_URL}${NC}"
    else
        echo -e "${YELLOW}    ⚠️ Worker server not reachable at ${BASE_URL}${NC}"
    fi
    
    if curl -s -o /dev/null --connect-timeout 5 "${MCP_URL}/health" 2>/dev/null; then
        echo -e "${GREEN}    ✅ MCP server reachable at ${MCP_URL}${NC}"
    else
        echo -e "${YELLOW}    ⚠️ MCP server not reachable at ${MCP_URL}${NC}"
    fi
    echo ""
fi

# Execute
if "${CMD[@]}" 2>&1 | tee -a "$OUTPUT_FILE"; then
    echo -e "${GREEN}  ✅ SIMD batch step completed${NC}"
else
    echo -e "${RED}  ❌ SIMD batch step failed${NC}"
    exit 1
fi

echo ""

# ─── Show results ──────────────────────────────────────────────────
if [[ -f "$OUTPUT_FILE" ]]; then
    echo -e "${BLUE}🔷 Results:${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    # Try to parse JSON if jq is available
    if command -v jq >/dev/null 2>&1; then
        if jq -e . "$OUTPUT_FILE" >/dev/null 2>&1; then
            echo -e "${CYAN}"
            jq -r '
                if .status then "  Status: \(.status)" else empty end,
                if .branch then "  Branch: \(.branch)" else empty end,
                if .coherence then "  Coherence: \(.coherence)" else empty end,
                if .phase then "  Phase: \(.phase)" else empty end,
                if .trace then "  Trace: \(.trace)" else empty end,
                if .merkle_root then "  Merkle Root: \(.merkle_root[:32])..." else empty end,
                if .seal then "  Seal: \(.seal)" else empty end
            ' "$OUTPUT_FILE" 2>/dev/null || cat "$OUTPUT_FILE"
            echo -e "${NC}"
        else
            echo -e "${YELLOW}  Output is not valid JSON${NC}"
            tail -20 "$OUTPUT_FILE"
        fi
    else
        echo -e "${YELLOW}  jq not available; showing raw output${NC}"
        tail -20 "$OUTPUT_FILE"
    fi
fi
echo ""

# ─── Summary ──────────────────────────────────────────────────────
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  S I M D   D E P L O Y   —   E N T R Y   8 7 9 4   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ SIMD batch step complete${NC}"
echo -e "${CYAN}📁 Output: ${OUTPUT_FILE}${NC}"
echo -e "${CYAN}🌐 Branch: ${BRANCH}${NC}"
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
