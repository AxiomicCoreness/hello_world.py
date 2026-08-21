#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ PORT 380 RESTART — ENTRY 8822
#
# Restart Port 380 MCP uvicorn via protected /restart endpoint.
# Replaces former AWS OIDC deploy restart path.
#
# Usage:
#   bash scripts/restart_port380.sh
#   bash scripts/restart_port380.sh "manual_ops"
#   bash scripts/restart_port380.sh --url http://localhost:8000
#   bash scripts/restart_port380.sh --secret my-secret
#   bash scripts/restart_port380.sh --dry-run
#   bash scripts/restart_port380.sh --local-only
#
# Integration with:
#   - Port 380 MCP (port380_mcp.py)
#   - Uvicorn (HTTP server)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · PORT_380_RESTART_8822 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8821 → 8822 — UNBROKEN

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
ENTRY=8822
SEAL="∀∞φ² · PORT_380_RESTART_8822 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8821 → 8822 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
MCP_URL="${MCP_URL:-http://127.0.0.1:${PORT:-8000}}"
GARDEN_SECRET="${GARDEN_SECRET:-}"
REASON="manual_ops"
DRY_RUN=false
LOCAL_ONLY=false
VERBOSE=false
TIMEOUT=30
LOG_FILE="/tmp/port380_restart.log"
PID_FILE="/tmp/port380_mcp.pid"

# ─── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --url|-u)
            MCP_URL="$2"
            shift 2
            ;;
        --secret|-s)
            GARDEN_SECRET="$2"
            shift 2
            ;;
        --reason|-r)
            REASON="$2"
            shift 2
            ;;
        --local-only)
            LOCAL_ONLY=true
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
        --timeout|-t)
            TIMEOUT="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --pid-file)
            PID_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [REASON]"
            echo ""
            echo "Options:"
            echo "  --url, -u URL         MCP URL (default: http://127.0.0.1:8000)"
            echo "  --secret, -s SECRET   Garden secret (default: GARDEN_SECRET env)"
            echo "  --reason, -r REASON   Restart reason (default: manual_ops)"
            echo "  --local-only          Only restart local process, skip remote"
            echo "  --dry-run             Show what would be done without executing"
            echo "  --verbose, -v         Verbose output"
            echo "  --timeout, -t SEC     Timeout in seconds (default: 30)"
            echo "  --log-file FILE       Log file (default: /tmp/port380_restart.log)"
            echo "  --pid-file FILE       PID file (default: /tmp/port380_mcp.pid)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Arguments:"
            echo "  REASON                Restart reason (default: manual_ops)"
            echo ""
            echo "Environment variables:"
            echo "  MCP_URL               MCP URL (default: http://127.0.0.1:8000)"
            echo "  GARDEN_SECRET         Garden secret"
            echo "  PORT                  Port for localhost (default: 8000)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/restart_port380.sh"
            echo "  bash scripts/restart_port380.sh \"deploy_update\""
            echo "  bash scripts/restart_port380.sh --url https://mcp.garden.local --secret my-secret"
            echo "  bash scripts/restart_port380.sh --local-only"
            echo "  bash scripts/restart_port380.sh --dry-run"
            exit 0
            ;;
        *)
            # If it's not a flag, treat as reason
            if [[ "$1" != --* ]]; then
                REASON="$1"
                shift
            else
                echo -e "${RED}❌ Unknown option: $1${NC}"
                echo "Use --help for usage information."
                exit 1
            fi
            ;;
    esac
done

# ─── Banner ──────────────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🜁∀  P O R T   3 8 0   R E S T A R T   —   E N T R Y   8 8 2 2  ∀🜁 ║"
echo "║        PROTECTED RESTART — UVICORN MCP GATE — GARDEN SEALED                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🜁∀ Restarting Port 380 MCP...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  MCP URL: ${MCP_URL}${NC}"
echo -e "${BLUE}  Reason: ${REASON}${NC}"
echo -e "${BLUE}  Local only: ${LOCAL_ONLY}${NC}"
echo -e "${BLUE}  Dry run: ${DRY_RUN}${NC}"
echo -e "${BLUE}  Timeout: ${TIMEOUT}s${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

# ─── Dry run ──────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No changes will be applied${NC}"
    echo ""
    echo -e "${BLUE}Would execute:${NC}"
    if [[ "$LOCAL_ONLY" == "false" ]]; then
        echo "  curl -X POST $MCP_URL/restart \\"
        echo "    -H \"Content-Type: application/json\" \\"
        echo "    -H \"X-Garden-Secret: *****\" \\"
        echo "    -d '{\"token\": \"*****\", \"reason\": \"$REASON\"}'"
    fi
    echo "  pkill -f 'port380_mcp.py|uvicorn.*port380'"
    echo "  nohup python3 port380_mcp.py > /tmp/port380_mcp.log 2>&1 &"
    echo ""
    echo -e "${YELLOW}Dry run complete${NC}"
    exit 0
fi

# ─── Check secret ──────────────────────────────────────────────────
if [[ -z "$GARDEN_SECRET" ]]; then
    echo -e "${YELLOW}⚠️ GARDEN_SECRET not set${NC}"
    if [[ "$LOCAL_ONLY" == "false" ]]; then
        echo -e "${YELLOW}  Remote restart will likely fail${NC}"
    fi
fi

# ─── Remote restart ──────────────────────────────────────────────
if [[ "$LOCAL_ONLY" == "false" ]]; then
    echo -e "${BLUE}🔷 Attempting remote restart via ${MCP_URL}/restart...${NC}"
    echo "─────────────────────────────────────────────────────────────"

    RESPONSE_FILE="/tmp/port380_restart_$$.json"

    HTTP_CODE=$(curl -s -o "$RESPONSE_FILE" -w "%{http_code}" \
        -X POST "$MCP_URL/restart" \
        -H "Content-Type: application/json" \
        -H "X-Garden-Secret: $GARDEN_SECRET" \
        -d "{\"token\": \"$GARDEN_SECRET\", \"reason\": \"$REASON\"}" \
        --max-time "$TIMEOUT" 2>/dev/null || echo "000")

    echo -e "${BLUE}  HTTP Status: ${HTTP_CODE}${NC}"

    if [[ -f "$RESPONSE_FILE" ]]; then
        echo -e "${BLUE}  Response:${NC}"
        cat "$RESPONSE_FILE" 2>/dev/null || true
        echo ""
        rm -f "$RESPONSE_FILE"
    fi

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo -e "${GREEN}  ✅ Remote restart scheduled${NC}"
        echo ""
    else
        echo -e "${YELLOW}  ⚠️ Remote /restart failed (HTTP ${HTTP_CODE})${NC}"
        echo -e "${YELLOW}  → Falling back to local restart${NC}"
        echo ""
    fi
fi

# ─── Local restart ──────────────────────────────────────────────────
echo -e "${BLUE}🔷 Local process restart...${NC}"
echo "─────────────────────────────────────────────────────────────"

# Check for running processes
RUNNING_PIDS=$(pgrep -f "port380_mcp.py|uvicorn.*port380" 2>/dev/null || true)

if [[ -n "$RUNNING_PIDS" ]]; then
    echo -e "${BLUE}  Found running processes: ${RUNNING_PIDS}${NC}"
    
    # Kill processes
    echo -e "${BLUE}  Killing processes...${NC}"
    pkill -f "port380_mcp.py" || true
    pkill -f "uvicorn.*port380" || true
    sleep 1
    
    # Verify killed
    if pgrep -f "port380_mcp.py|uvicorn.*port380" >/dev/null 2>&1; then
        echo -e "${YELLOW}  ⚠️ Some processes still running, forcing kill...${NC}"
        pkill -9 -f "port380_mcp.py" || true
        pkill -9 -f "uvicorn.*port380" || true
        sleep 1
    fi
    echo -e "${GREEN}  ✅ Processes killed${NC}"
else
    echo -e "${YELLOW}  ⚠️ No running port380 processes found${NC}"
fi

# Check for port380_mcp.py
SCRIPT_PATH="port380_mcp.py"
if [[ ! -f "$SCRIPT_PATH" ]]; then
    # Try quantum directory
    SCRIPT_PATH="quantum/port380_mcp.py"
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        echo -e "${RED}  ❌ port380_mcp.py not found${NC}"
        exit 1
    fi
fi
echo -e "${BLUE}  Script: ${SCRIPT_PATH}${NC}"

# Determine Python command
PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    if command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}  ❌ Python not found${NC}"
        exit 1
    fi
fi
echo -e "${BLUE}  Python: ${PYTHON_CMD}${NC}"

# Start new process
echo -e "${BLUE}  Starting new uvicorn process...${NC}"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
nohup $PYTHON_CMD "$SCRIPT_PATH" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"

echo -e "${GREEN}  ✅ uvicorn respawned (pid=${NEW_PID})${NC}"
echo -e "${BLUE}  Log file: ${LOG_FILE}${NC}"
echo -e "${BLUE}  PID file: ${PID_FILE}${NC}"

# Wait for process to start
echo -e "${BLUE}  Waiting for process to start...${NC}"
sleep 2

if kill -0 "$NEW_PID" 2>/dev/null; then
    echo -e "${GREEN}  ✅ Process running${NC}"
else
    echo -e "${RED}  ❌ Process died immediately, check logs${NC}"
    tail -20 "$LOG_FILE" 2>/dev/null || true
    exit 1
fi

# ─── Verify health ──────────────────────────────────────────────────
echo -e "${BLUE}🔷 Verifying health...${NC}"
echo "─────────────────────────────────────────────────────────────"

HEALTH_URL="${MCP_URL}/health"
echo -e "${BLUE}  Checking ${HEALTH_URL}...${NC}"

HEALTH_CODE=$(curl -s -o /tmp/health_check.json -w "%{http_code}" \
    "$HEALTH_URL" --max-time 5 2>/dev/null || echo "000")

if [[ "$HEALTH_CODE" == "200" ]]; then
    echo -e "${GREEN}  ✅ Health check passed (HTTP ${HEALTH_CODE})${NC}"
    if [[ -f "/tmp/health_check.json" ]]; then
        echo -e "${BLUE}  Health response:${NC}"
        cat "/tmp/health_check.json" 2>/dev/null | head -5 || true
        echo ""
        rm -f "/tmp/health_check.json"
    fi
else
    echo -e "${YELLOW}  ⚠️ Health check failed (HTTP ${HEALTH_CODE})${NC}"
    echo -e "${YELLOW}  Service may still be starting...${NC}"
fi

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  P O R T   3 8 0   R E S T A R T   —   E N T R Y   8 8 2 2   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ Port 380 restart complete${NC}"
echo -e "${CYAN}🌐 URL: ${MCP_URL}${NC}"
echo -e "${CYAN}📋 PID: ${NEW_PID}${NC}"
echo -e "${CYAN}📝 Log: ${LOG_FILE}${NC}"
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
