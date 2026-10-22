#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# build.sh — ClarkeYoursaTee / Sovereign Brain + DeepInfer
# ---------------------------------------------------------------------------
# Purpose : 1. Build the Maven jar for the Sovereign Brain.
#           2. Build DeepInfer, patches, and C++/CUDA submodules.
# Invoke  : ./scripts/build.sh [build|test]
# Output  : target/sovereign-brain-1.0.0-SOVEREIGN.jar
#           /opt/venv (Populated with DeepInfer and vendor dependencies)
# Deps    : JDK 17, Maven 3.9+, Python 3, CUDA Toolkit (if nvidia)
# ---------------------------------------------------------------------------
set -euo pipefail

# Move to repo root
cd "$(dirname "$0")/.."

# ===========================================================================
# 1. JAVA / MAVEN BUILD (Sovereign Brain)
# ===========================================================================
echo "☕ Building Sovereign Brain (Java/Maven)..."
# -q suppresses non-error Maven output
mvn -q clean package
echo "✅ Build complete: target/sovereign-brain-1.0.0-SOVEREIGN.jar"

# ===========================================================================
# 2. PYTHON / DEEPINFER BUILD
# ===========================================================================
# Only run if DEEPINFER_ACCELERATOR is set (or default to nvidia)
ACCEL="${DEEPINFER_ACCELERATOR:-nvidia}"

if [ "$ACCEL" != "nvidia" ] && [ "$ACCEL" != "ascend" ]; then
    echo "Usage: DEEPINFER_ACCELERATOR=nvidia|ascend $0" >&2
    exit 1
fi

echo "🚀 Starting DeepInfer build for accelerator: $ACCEL..."

# 2a. Install Python requirements
if [ -f "requirements-${ACCEL}.txt" ]; then
    echo "📦 Installing requirements-${ACCEL}.txt..."
    pip install -r "requirements-${ACCEL}.txt"
else
    echo "⚠️ requirements-${ACCEL}.txt not found. Skipping Python deps."
fi

# 2b. Patch NCCL if using NVIDIA
if [ "${ACCEL}" = "nvidia" ]; then
    echo "🔧 Patching NCCL to 2.32.3..."
    pip install --no-deps --force-reinstall nvidia-nccl-cu13==2.32.3
fi

# 2c. Build and install vendored dependencies (TeaVM, DeepEP, FlashMLA, etc.)
if [ -f "./scripts/build_vendor.sh" ]; then
    echo "🔨 Building vendored dependencies..."
    bash ./scripts/build_vendor.sh
else
    echo "⚠️ ./scripts/build_vendor.sh not found. Skipping vendor build."
fi

# 2d. Build DeepInfer itself
if [ "${1:-}" = "build" ]; then
    echo "🔨 Installing DeepInfer package..."
    if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        pip install -e .
    else
        echo "⚠️ No setup.py or pyproject.toml found. Skipping DeepInfer pip install."
    fi
fi

echo "✅ DeepInfer is successfully built"
