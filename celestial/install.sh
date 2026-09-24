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

# ... (everything below unchanged) ...
