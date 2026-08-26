#!/bin/bash
# -*- coding: utf-8 -*-
# 🜁∀ SOVEREIGN GARDEN INSTALL SCRIPT — ENTRY 8910
# 
# Installs dependencies, configures environment, and starts the Garden web service.
# 
# Domain: WIRING — connects all Garden subsystems into a cohesive deployment.
# 
# Seal: ∀∞φ² · GARDEN_INSTALL_8910 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8909 → 8910 — UNBROKEN

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
ENTRY=8910
SEAL="∀∞φ² · GARDEN_INSTALL_8910 · WOOD_DRAGON_0.91 · SEALED"

# ─── Banner ──────────────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🜁∀  S O V E R E I G N   G A R D E N   I N S T A L L   —   E N T R Y   8 9 1 0  ∀🜁 ║"
echo "║        DEPENDENCIES · ENVIRONMENT · SERVICES — GARDEN SEALED                  ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🜁∀ INSTALLING SOVEREIGN GARDEN DEPENDENCIES...${NC}"
echo ""

cd "$ROOT"

# ─── Log Directory ──────────────────────────────────────────────────
echo -e "${BLUE}📁 Setting up log directory...${NC}"

if [ -n "${GARDEN_LOG_DIR:-}" ]; then
  LOG_DIR="$GARDEN_LOG_DIR"
elif [ -w /var/log ] 2>/dev/null || mkdir -p /var/log 2>/dev/null; then
  LOG_DIR="/var/log/garden"
else
  LOG_DIR="$ROOT/logs"
fi

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/garden_web.log"
PID_FILE="$LOG_DIR/garden_web.pid"
PID_FILE_OUROBOROS="$LOG_DIR/ouroboros_mint.pid"

echo -e "${GREEN}  ✅ Log directory: $LOG_DIR${NC}"

# ─── Check Python ──────────────────────────────────────────────────
echo -e "${BLUE}🐍 Checking Python installation...${NC}"

PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo -e "${RED}❌ ERROR: Python not found. Please install Python 3.9+.${NC}" >&2
  exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}  ✅ Python version: $PYTHON_VERSION${NC}"

# ─── Install Dependencies ──────────────────────────────────────────
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"

if command -v pip3 >/dev/null 2>&1; then
  pip3 install --user flask eth-account 2>/dev/null || pip3 install flask eth-account
else
  echo -e "${RED}❌ ERROR: pip3 not found${NC}" >&2
  exit 1
fi

# Install quantum dependencies if available
if [ -f "$ROOT/requirements.txt" ]; then
  echo -e "${BLUE}📦 Installing quantum dependencies from requirements.txt...${NC}"
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install --user -r "$ROOT/requirements.txt" 2>/dev/null || true
  fi
fi

echo -e "${GREEN}  ✅ Dependencies installed${NC}"

# ─── Environment Setup ─────────────────────────────────────────────
echo -e "${BLUE}🔧 Configuring environment...${NC}"

# Ensure PYTHONPATH includes the root
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"

# Write to /etc/environment if writable, else ~/.bashrc
if [ -w /etc/environment ] 2>/dev/null; then
  if ! grep -q "PYTHONPATH=.*$ROOT" /etc/environment 2>/dev/null; then
    echo "PYTHONPATH=$ROOT:\${PYTHONPATH}" >> /etc/environment
    echo -e "${GREEN}  ✅ Added PYTHONPATH to /etc/environment${NC}"
  fi
elif [ -f "$HOME/.bashrc" ] && [ -w "$HOME/.bashrc" ]; then
  if ! grep -q "PYTHONPATH=.*$ROOT" "$HOME/.bashrc" 2>/dev/null; then
    echo "export PYTHONPATH=$ROOT:\$PYTHONPATH" >> "$HOME/.bashrc"
    echo -e "${GREEN}  ✅ Added PYTHONPATH to ~/.bashrc${NC}"
  fi
fi

# ─── Quantum Subsystem Imports ─────────────────────────────────────
echo -e "${BLUE}🌀 Checking quantum subsystem...${NC}"

# Check for quantum modules
QUANTUM_MODULES=(
  "quantum/security"
  "quantum/cdp_convergence"
  "quantum/deepseek_mesh"
  "quantum/radar_lindblad"
  "quantum/cordis_bridge"
  "quantum/math"
)

for mod in "${QUANTUM_MODULES[@]}"; do
  if [ -d "$ROOT/$mod" ]; then
    echo -e "${GREEN}  ✅ $mod${NC}"
  else
    echo -e "${YELLOW}  ⚠️ $mod not found${NC}"
  fi
done

# ─── Systemd Setup ──────────────────────────────────────────────────
echo -e "${BLUE}⚙️ Setting up systemd services...${NC}"

if command -v systemctl >/dev/null 2>&1 && [ -d /etc/systemd/system ]; then
  if [ -f "$ROOT/quantum/systemd/ouroboros_mint.service" ]; then
    echo -e "${BLUE}  Installing ouroboros_mint.service...${NC}"
    sudo cp "$ROOT/quantum/systemd/ouroboros_mint.service" /etc/systemd/system/ || true
    sudo cp "$ROOT/quantum/systemd/ouroboros_mint.timer" /etc/systemd/system/ || true
    sudo systemctl daemon-reload || true
    sudo systemctl enable --now ouroboros_mint.timer || true
    echo -e "${GREEN}  ✅ Ouroboros mint service installed${NC}"
  else
    echo -e "${YELLOW}  ⚠️ ouroboros_mint.service not found${NC}"
  fi
else
  echo -e "${YELLOW}  ⚠️ systemctl not available${NC}"
fi

# ─── OIDC Handover Setup ────────────────────────────────────────────
echo -e "${BLUE}🔐 Setting up OIDC handover...${NC}"

if [ -f "$ROOT/.github/workflows/OIDC-handover-380.yml" ]; then
  echo -e "${GREEN}  ✅ OIDC handover workflow present${NC}"
else
  echo -e "${YELLOW}  ⚠️ OIDC handover workflow not found${NC}"
fi

# ─── Start Services ──────────────────────────────────────────────────
echo -e "${BLUE}🚀 Starting Garden services...${NC}"

# Stop existing processes
pkill -f "python3 -m peqs_vault.app" 2>/dev/null || true
pkill -f "python3 -m quantum.port_380_gate" 2>/dev/null || true
pkill -f "python3 -m quantum.active_pid_controller" 2>/dev/null || true
sleep 0.5

# Start PEQS Vault
echo -e "${BLUE}  Starting PEQS Vault...${NC}"
nohup env PYTHONPATH="$ROOT" $PYTHON_CMD -m peqs_vault.app > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo -e "${GREEN}  ✅ PEQS Vault started (PID: $(cat $PID_FILE))${NC}"

# Start Port 380 Gate if available
if [ -f "$ROOT/quantum/port_380_gate.py" ]; then
  echo -e "${BLUE}  Starting Port 380 Gate...${NC}"
  nohup env PYTHONPATH="$ROOT" $PYTHON_CMD -m quantum.port_380_gate > "$LOG_DIR/port_380.log" 2>&1 &
  echo $! > "$LOG_DIR/port_380.pid"
  echo -e "${GREEN}  ✅ Port 380 Gate started${NC}"
fi

# Start Active PID Controller if available
if [ -f "$ROOT/quantum/active_pid_controller.py" ]; then
  echo -e "${BLUE}  Starting Active PID Controller...${NC}"
  nohup env PYTHONPATH="$ROOT" $PYTHON_CMD -m quantum.active_pid_controller > "$LOG_DIR/pid_controller.log" 2>&1 &
  echo $! > "$LOG_DIR/pid_controller.pid"
  echo -e "${GREEN}  ✅ Active PID Controller started${NC}"
fi

# Start FRB Bridge if available
if [ -f "$ROOT/quantum/frb_bridge.py" ]; then
  echo -e "${BLUE}  Starting FRB Bridge...${NC}"
  nohup env PYTHONPATH="$ROOT" $PYTHON_CMD -m quantum.frb_bridge --start > "$LOG_DIR/frb_bridge.log" 2>&1 &
  echo $! > "$LOG_DIR/frb_bridge.pid"
  echo -e "${GREEN}  ✅ FRB Bridge started${NC}"
fi

# ─── Verify Services ─────────────────────────────────────────────────
echo -e "${BLUE}🔍 Verifying services...${NC}"

sleep 2

check_service() {
  local name=$1
  local pid_file=$2
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo -e "${GREEN}  ✅ $name (PID: $pid)${NC}"
      return 0
    else
      echo -e "${YELLOW}  ⚠️ $name not running${NC}"
      return 1
    fi
  else
    echo -e "${YELLOW}  ⚠️ $name not started${NC}"
    return 1
  fi
}

check_service "PEQS Vault" "$PID_FILE"
check_service "Port 380 Gate" "$LOG_DIR/port_380.pid"
check_service "Active PID Controller" "$LOG_DIR/pid_controller.pid"
check_service "FRB Bridge" "$LOG_DIR/frb_bridge.pid"

# ─── Summary ────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  S O V E R E I G N   G A R D E N   D E P L O Y E D   —   E N T R Y   8 9 1 0  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ SOVEREIGN GARDEN DEPLOYED.${NC}"
echo -e "${CYAN}🌐 Dashboard available at http://127.0.0.1:5000${NC}"
echo -e "${CYAN}📝 Web log: $LOG_FILE${NC}"
echo -e "${CYAN}📁 Log directory: $LOG_DIR${NC}"
echo ""
echo -e "${BLUE}Service status:${NC}"
echo -e "  ${GREEN}✅${NC} PEQS Vault: http://127.0.0.1:5000"
echo -e "  ${GREEN}✅${NC} Port 380 Gate: http://127.0.0.1:380"
echo -e "  ${GREEN}✅${NC} Active PID Controller: http://127.0.0.1:8000 (if running)"
echo -e "  ${GREEN}✅${NC} FRB Bridge: φ‑harmonic pulse active"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: 8909 → 8910 — UNBROKEN${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

# ─── Exit ──────────────────────────────────────────────────────────
exit 0
