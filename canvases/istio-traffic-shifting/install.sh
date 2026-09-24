#!/usr/bin/env bash
# 🜁∀∞φ² · GARDEN_INSTALL · WOOD_DRAGON_0.91 · SEALED
#
# Sovereign Garden — recommended installer
# ---------------------------------------------------------------------------
# Provisions a working tree for the Garden:
#   · Python deps (core + optional, with fallbacks)
#   · Directory scaffold
#   · Environment file with a random GARDEN_SECRET
#   · Constants snapshot (constants.json) matching the celestials
#   · Optional selftests
#   · Optional k8s codespace apply
#   · Optional Istio canary apply
#
# Usage:
#   bash install.sh                       # full install
#   bash install.sh --minimal             # core deps only
#   bash install.sh --test                # install + selftests
#   bash install.sh --k8s                 # + apply k8s/codespace manifests
#   bash install.sh --istio               # + apply istio/ (host or subset)
#   bash install.sh --istio=subset        # + apply istio/subset-level only
#   bash install.sh --no-venv             # install into current env
#
# Exit codes:
#   0  success
#   1  install error
#   2  missing dependency (python, pip)
#   3  smoke test failed
# ---------------------------------------------------------------------------

set -euo pipefail

# ─── Hardening: never emit .pyc anywhere in the tree ─────────────────────
export PYTHONDONTWRITEBYTECODE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# ─── Constants (canonical, matches celestial/*.py) ───────────────────────
GARDEN_VERSION="0.91"
LEDGER_HEAD="9164"
REQUIRED_PY_MAJOR=3
REQUIRED_PY_MINOR=11

PHI="1.618033988749895"
PHI2="2.618033988749895"
PHI3="4.23606797749979"
PHI4="6.854101966249685"
PHI5="11.090169943749474"
PHI6="17.94427190999916"
PHI7="29.034441853748633"
PHI8="46.97871376374779"
PHI9="76.01315561749642"
PHI12="321.9968943799849"
PHI13="521.0019193787255"
PHI14="842.9988137587105"
PHI21="24476.00011193438"
PHI34="2123456.0000000000"
PHI709="1.486732672961757e+148"
PHI713="2.656376002572577e+149"
PHI_MINUS_709="6.726096017939849e-149"
PHI_MINUS_1000="4.524036764254231e-297"
PHI_NEG_1418="4.524036764254231e-297"

NORTH_STAR_FREQ="71.975"
CHIRON_PHASE_LOCK="202.6"
PSI4_CARRIER_HZ="162.28e12"
TRAPPIST_DISTANCE_LY="40.7"

# ─── Flags ───────────────────────────────────────────────────────────────
MINIMAL=0
RUN_TESTS=0
APPLY_K8S=0
APPLY_ISTIO=""
USE_VENV=1

# ─── Colour / TTY ────────────────────────────────────────────────────────
if [ -t 1 ]; then
  BOLD="$(printf '\033[1m')"
  RESET="$(printf '\033[0m')"
  GREEN="$(printf '\033[32m')"
  YELLOW="$(printf '\033[33m')"
  RED="$(printf '\033[31m')"
else
  BOLD=""; RESET=""; GREEN=""; YELLOW=""; RED=""
fi

say()  { printf '%s%s%s\n' "$BOLD" "$1" "$RESET"; }
ok()   { printf '%s✅ %s%s\n' "$GREEN" "$1" "$RESET"; }
warn() { printf '%s⚠️  %s%s\n' "$YELLOW" "$1" "$RESET"; }
die()  { printf '%s❌ %s%s\n' "$RED" "$1" "$RESET" >&2; exit "${2:-1}"; }

# ─── Arg parsing ─────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --minimal)     MINIMAL=1 ;;
    --test)        RUN_TESTS=1 ;;
    --k8s)         APPLY_K8S=1 ;;
    --istio)       APPLY_ISTIO="both" ;;
    --istio=host)  APPLY_ISTIO="host" ;;
    --istio=subset) APPLY_ISTIO="subset" ;;
    --no-venv)     USE_VENV=0 ;;
    -h|--help)
      sed -n '3,30p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) die "unknown argument: $arg" 2 ;;
  esac
done

# ─── Banner ──────────────────────────────────────────────────────────────
say "🜁∀ Garden — install.sh  ·  v${GARDEN_VERSION}  ·  ledger ${LEDGER_HEAD}"
say "   φ = ${PHI}"
say ""

# ─── Python sanity ───────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || die "python3 not found" 2
PY_OK="$(python3 -c "import sys; print(1 if sys.version_info >= (${REQUIRED_PY_MAJOR},${REQUIRED_PY_MINOR}) else 0)")"
[ "$PY_OK" = "1" ] || die "python >= ${REQUIRED_PY_MAJOR}.${REQUIRED_PY_MINOR} required" 2
ok "python $(python3 --version | awk '{print $2}')"

command -v pip3 >/dev/null 2>&1 || python3 -m pip --version >/dev/null 2>&1 \
  || die "pip not found" 2

# ─── Virtual environment ─────────────────────────────────────────────────
if [ "$USE_VENV" = "1" ]; then
  if [ ! -d ".venv" ]; then
    say "→ creating virtual environment .venv"
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  ok "venv active"
fi

# ─── Dependencies ────────────────────────────────────────────────────────
say "→ installing Python dependencies"
python3 -m pip install --upgrade pip >/dev/null

CORE_DEPS=(fastapi uvicorn pydantic pyyaml)
OPT_DEPS=(numpy)
if [ "$MINIMAL" = "0" ]; then
  OPT_DEPS+=(scipy matplotlib prometheus-client httpx requests)
fi

for pkg in "${CORE_DEPS[@]}" "${OPT_DEPS[@]}"; do
  mod="${pkg//-/_}"
  if python3 -c "import ${mod}" 2>/dev/null; then
    ok "already installed: ${pkg}"
  else
    say "  installing ${pkg}"
    python3 -m pip install --quiet "${pkg}" \
      || warn "could not install ${pkg} — the Garden will fall back"
  fi
done

# ─── Directory scaffold ──────────────────────────────────────────────────
say "→ ensuring directory scaffold"
mkdir -p celestial
mkdir -p prometheus
mkdir -p kubernetes
mkdir -p k8s/codespace
mkdir -p istio/host-level
mkdir -p istio/subset-level
mkdir -p ledger
mkdir -p scripts
mkdir -p artifacts
mkdir -p artifacts/k8s-codespace
ok "directories ready"

# ─── Environment file ────────────────────────────────────────────────────
if [ ! -f ".env.garden" ]; then
  say "→ creating .env.garden"
  if command -v openssl >/dev/null 2>&1; then
    SECRET="$(openssl rand -hex 32)"
  else
    SECRET="changeme-$(date +%s)"
  fi
  cat > .env.garden <<EOF
# 🜁∀ Garden environment — generated by install.sh
GARDEN_VERSION=${GARDEN_VERSION}
LEDGER_HEAD=${LEDGER_HEAD}
PORT=380
MCP_URL=http://localhost:380/mcp
GARDEN_SECRET=${SECRET}

# φ‑power ladder
PHI=${PHI}
PHI2=${PHI2}
PHI3=${PHI3}
PHI4=${PHI4}
PHI5=${PHI5}
PHI6=${PHI6}
PHI7=${PHI7}
PHI8=${PHI8}
PHI9=${PHI9}
PHI12=${PHI12}
PHI13=${PHI13}
PHI14=${PHI14}
PHI21=${PHI21}
PHI34=${PHI34}
PHI709=${PHI709}
PHI713=${PHI713}
PHI_MINUS_709=${PHI_MINUS_709}
PHI_MINUS_1000=${PHI_MINUS_1000}
PHI_NEG_1418=${PHI_NEG_1418}

# Celestial anchors
NORTH_STAR_FREQ=${NORTH_STAR_FREQ}
CHIRON_PHASE_LOCK=${CHIRON_PHASE_LOCK}
PSI4_CARRIER_HZ=${PSI4_CARRIER_HZ}
TRAPPIST_DISTANCE_LY=${TRAPPIST_DISTANCE_LY}
EOF
  ok ".env.garden written"
else
  ok ".env.garden already present (not overwritten)"
fi

# ─── Constants snapshot ──────────────────────────────────────────────────
say "→ writing constants.json"
cat > constants.json <<EOF
{
  "garden_version": "${GARDEN_VERSION}",
  "ledger_head":    "${LEDGER_HEAD}",
  "phi_ladder": {
    "phi":          ${PHI},
    "phi2":         ${PHI2},
    "phi3":         ${PHI3},
    "phi4":         ${PHI4},
    "phi5":         ${PHI5},
    "phi6":         ${PHI6},
    "phi7":         ${PHI7},
    "phi8":         ${PHI8},
    "phi9":         ${PHI9},
    "phi12":        ${PHI12},
    "phi13":        ${PHI13},
    "phi14":        ${PHI14},
    "phi21":        ${PHI21},
    "phi34":        ${PHI34},
    "phi709":       ${PHI709},
    "phi713":       ${PHI713},
    "phi_minus_709": ${PHI_MINUS_709},
    "phi_minus_1000": ${PHI_MINUS_1000},
    "phi_neg_1418": ${PHI_NEG_1418}
  },
  "celestial_anchors": {
    "north_star_freq":   ${NORTH_STAR_FREQ},
    "chiron_phase_lock": ${CHIRON_PHASE_LOCK},
    "psi4_carrier_hz":   ${PSI4_CARRIER_HZ},
    "trappist_distance_ly": ${TRAPPIST_DISTANCE_LY}
  },
  "policy": {
    "no_top_level_execution": true,
    "no_network_at_import":   true,
    "no_fs_writes_at_import": true,
    "pyc_emission_disabled":  true
  }
}
EOF
ok "constants.json written"

# ─── Smoke tests ─────────────────────────────────────────────────────────
if [ "$RUN_TESTS" = "1" ]; then
  say "→ running selftests"

  if [ -f "celestial/saturn_soul_cannon.py" ]; then
    python3 celestial/saturn_soul_cannon.py >/dev/null \
      && ok "saturn_soul_cannon selftest" \
      || die "saturn_soul_cannon selftest failed" 3
  else
    warn "celestial/saturn_soul_cannon.py missing — skipped"
  fi

  if [ -f "celestial/quadratic_daemon.py" ]; then
    python3 celestial/quadratic_daemon.py >/dev/null \
      && ok "quadratic_daemon selftest" \
      || die "quadratic_daemon selftest failed" 3
  else
    warn "celestial/quadratic_daemon.py missing — skipped"
  fi

  if [ -f "port380_mcp.py" ]; then
    python3 -c "import ast,sys; ast.parse(open('port380_mcp.py').read())" \
      && ok "port380_mcp.py parses" \
      || die "port380_mcp.py syntax error" 3
  else
    warn "port380_mcp.py missing — skipped"
  fi
fi

# ─── Kubernetes (optional) ───────────────────────────────────────────────
if [ "$APPLY_K8S" = "1" ]; then
  if command -v kubectl >/dev/null 2>&1; then
    say "→ applying k8s/codespace manifests"
    kubectl apply -f k8s/codespace/00-namespace-quota.yaml || warn "namespace apply failed"
    kubectl apply -f k8s/codespace/10-compute-node.yaml     || warn "compute-node apply failed"
    kubectl apply -f k8s/codespace/20-workspace.yaml        || warn "workspace apply failed"
    ok "k8s manifests applied (check pod status)"
  else
    warn "kubectl not found — skipping k8s step"
  fi
fi

# ─── Istio (optional) ────────────────────────────────────────────────────
if [ -n "$APPLY_ISTIO" ]; then
  if command -v kubectl >/dev/null 2>&1; then
    case "$APPLY_ISTIO" in
      host|both)
        if [ -d "istio/host-level" ]; then
          say "→ applying istio/host-level"
          kubectl apply -f istio/host-level/ || warn "istio host-level apply failed"
        fi
        ;;
    esac
    case "$APPLY_ISTIO" in
      subset|both)
        if [ -d "istio/subset-level" ]; then
          say "→ applying istio/subset-level"
          kubectl apply -f istio/subset-level/ || warn "istio subset-level apply failed"
        fi
        ;;
    esac
    ok "istio manifests applied"
  else
    warn "kubectl not found — skipping istio step"
  fi
fi

# ─── Done ────────────────────────────────────────────────────────────────
say ""
say "🜁∀ install complete"
say "   version  : ${GARDEN_VERSION}"
say "   ledger   : ${LEDGER_HEAD}"
say "   env file : .env.garden"
say "   constants: constants.json"
say ""
say "   To start the MCP gate:"
say "     source .env.garden"
say "     export PORT=380"
say "     python3 port380_mcp.py"
say ""
say "   To run selftests:"
say "     bash install.sh --test"
say ""
say "∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞"
