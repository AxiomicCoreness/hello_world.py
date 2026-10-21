#!/usr/bin/env bash
# 🜁∀∞φ² · GARDEN_INSTALL · WOOD_DRAGON_0.91 · SEALED
#
# Sovereign Garden — installer
# ---------------------------------------------------------------------------
# Provisions a working tree for the Garden: Python deps, directory scaffold,
# environment file, and a smoke test.
#
# Usage:
#   bash install.sh               # full install
#   bash install.sh --minimal     # core only (no scipy / matplotlib)
#   bash install.sh --test        # install + run selftests
#   bash install.sh --k8s         # additionally apply k8s/codespace manifests
#   bash install.sh --no-venv     # install into current environment
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

# ─── Trap for graceful exit ──────────────────────────────────────────────
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Installer failed with exit code $exit_code" >&2
    fi
}
trap cleanup EXIT

# ─── CLI Parsing ─────────────────────────────────────────────────────────
MINIMAL=0
RUN_TESTS=0
APPLY_K8S=0
USE_VENV=1

for arg in "$@"; do
    case $arg in
        --minimal) MINIMAL=1 ;;
        --test)    RUN_TESTS=1 ;;
        --k8s)     APPLY_K8S=1 ;;
        --no-venv) USE_VENV=0 ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

# ─── Dependency Checks ───────────────────────────────────────────────────
echo "🔍 Checking system dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is not installed." >&2
    exit 2
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed." >&2
    exit 2
fi

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   ✅ Found Python $PYTHON_VER"

# ─── Virtual Environment ─────────────────────────────────────────────────
if [ "$USE_VENV" -eq 1 ]; then
    if ! python3 -c 'import venv' &> /dev/null; then
        echo "❌ python3-venv is missing. Install it or use --no-venv." >&2
        exit 2
    fi
    
    if [ ! -d ".venv" ]; then
        echo "🐍 Creating virtual environment..."
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    echo "   ✅ venv active"
fi

# ─── Install Python Dependencies ─────────────────────────────────────────
echo "📦 Installing Python dependencies..."

pip install --upgrade pip > /dev/null

if [ "$MINIMAL" -eq 1 ]; then
    echo "   (minimal mode — skipping scipy/matplotlib)"
    pip install fastapi uvicorn pydantic pyyaml pytest numpy requests
else
    pip install fastapi uvicorn pydantic pyyaml pytest numpy requests scipy matplotlib
fi

echo "   ✅ Dependencies installed."

# ─── Scaffold Directories ────────────────────────────────────────────────
echo "📂 Scaffolding directory tree..."

mkdir -p ledger
mkdir -p anatomy
mkdir -p app/routes
mkdir -p argocd
mkdir -p automation
mkdir -p .github/workflows

echo "   ✅ Directories verified."

# ─── Environment File ────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "📝 Creating default .env..."
    cat > .env << 'EOF'
# Sovereign Garden Environment Defaults
BIND_HOST=127.0.0.1
BIND_PORT_START=8000
BIND_PORT_END=8000
PHASE_LOCK=202.6
GARDEN_SECRET=
EOF
    echo "   ✅ .env created."
else
    echo "   ⚠️  .env already exists, skipping."
fi

# ─── Run Smoke Tests ─────────────────────────────────────────────────────
if [ "$RUN_TESTS" -eq 1 ]; then
    echo "🧪 Running smoke tests..."
    
    # 1. Verify imports work
    if ! python3 -c "import anatomy.body; import app.config; print('   ✅ Imports OK')"; then
        echo "❌ Import smoke test failed." >&2
        exit 3
    fi
    
    # 2. Verify loopback security is active
    if ! python3 -c "from anatomy.body import assert_loopback; assert_loopback('127.0.0.1'); print('   ✅ Loopback policy OK')"; then
        echo "❌ Loopback smoke test failed." >&2
        exit 3
    fi
    
    # 3. Run pytest if tests exist
    if [ -d "tests" ]; then
        pytest tests/ -q
    fi
    
    echo "   ✅ All smoke tests passed."
fi

# ─── K8s Manifest Deployment ─────────────────────────────────────────────
if [ "$APPLY_K8S" -eq 1 ]; then
    echo "☸️  Applying K8s manifests..."
    
    if ! command -v kubectl &> /dev/null; then
        echo "⚠️  kubectl not found. Skipping K8s deployment."
    else
        kubectl apply -f argocd/
        echo "   ✅ K8s manifests applied."
    fi
fi

echo ""
echo "🜁∀∞φ² · GARDEN_INSTALL COMPLETE"
echo "   To start the API:"
if [ "$USE_VENV" -eq 1 ]; then
    echo "     source .venv/bin/activate"
fi
echo "     python axiomiccoreness/github.io/hello_world.py"
echo ""
