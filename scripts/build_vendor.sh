#!/bin/bash
set -euo pipefail

echo "📦 Building vendored components..."

# Ensure we are in the repo root
cd "$(dirname "$0")/.."

# ==========================================
# 1. TeaVM Sync (Java/Maven)
# ==========================================
if [ -d "vendor/teavm-sync" ]; then
    echo "☕ Building TeaVM Sync..."
    cd vendor/teavm-sync
    # Assuming TeaVM sync uses Maven
    mvn clean install -DskipTests
    cd ../..
fi

# ==========================================
# 2. Backend Workers (Python)
# ==========================================
if [ -d "vendor/backend-workers" ]; then
    echo "🐍 Building Backend Workers..."
    # Install as editable package or run their setup script
    if [ -f "vendor/backend-workers/requirements.txt" ]; then
        pip install -r vendor/backend-workers/requirements.txt
    fi
    if [ -f "vendor/backend-workers/setup.py" ] || [ -f "vendor/backend-workers/pyproject.toml" ]; then
        pip install -e vendor/backend-workers
    fi
fi

# ==========================================
# 3. DeepSeek Vendored Components (C++/CUDA)
# ==========================================
if [ -d "vendor/DeepSelect" ]; then
    echo "🔨 Building DeepSelect..."
    pip install -e vendor/DeepSelect
fi

if [ "${DEEPINFER_ACCELERATOR:-nvidia}" = "nvidia" ]; then
    echo "🟢 Building NVIDIA components..."
    if [ -d "vendor/DeepEP" ]; then pip install -e vendor/DeepEP; fi
    if [ -d "vendor/DeepGEMM" ]; then pip install -e vendor/DeepGEMM; fi
    if [ -d "vendor/FlashMLA" ]; then pip install -e vendor/FlashMLA; fi

elif [ "${DEEPINFER_ACCELERATOR:-}" = "ascend" ]; then
    echo "🔴 Building Ascend components..."
    if [ -d "vendor/DeepEP-Ascend" ]; then pip install -e vendor/DeepEP-Ascend; fi
    if [ -d "vendor/DeepGEMM-Ascend" ]; then pip install -e vendor/DeepGEMM-Ascend; fi
fi

echo "✅ All vendored components successfully built."
