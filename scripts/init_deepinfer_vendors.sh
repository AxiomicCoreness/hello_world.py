#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# init_deepinfer_vendors.sh — clone DeepInfer + kernels at pinned SHAs
# ---------------------------------------------------------------------------
# Pins recorded from deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9
# Does not invent SHAs. Does not push. Safe to re-run (idempotent checkout).
# After success, record gitlinks:
#   git add vendor/DeepInfer vendor/DeepGEMM vendor/FlashMLA vendor/DeepEP \
#           vendor/DeepSelect vendor/DeepGEMM-Ascend vendor/DeepEP-Ascend
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEEPINFER_SHA="9bd9cf243fc53ef9afbf8f04d391d989117d6ab9"
DEEPGEMM_SHA="1fc9c66975ee322d628b3288534ca0e9ce12a64d"
FLASHMLA_SHA="2e5429fc5653bab6e081f09477126f731882a6a9"
DEEPEP_SHA="f6aa38fe06cd4a0489e7730365d4e0114970a2f3"
DEEPSELECT_SHA="bfa4507d935f17ebfc3d0f00ff7d3c9a4d0e5c18"
DEEPGEMM_ASCEND_SHA="3a35326271b069b8b5bf1a754435acd6cc91575b"
DEEPEP_ASCEND_SHA="3b25377d04b24fc6154698ded78a2bcb2c59afff"

clone_at() {
  local path="$1" url="$2" sha="$3"
  mkdir -p "$(dirname "$path")"
  if [ ! -d "$path/.git" ]; then
    echo "→ cloning $url into $path"
    git clone --no-checkout "$url" "$path"
  else
    echo "→ reusing existing $path"
  fi
  (
    cd "$path"
    git fetch --depth 1 origin "$sha" 2>/dev/null \
      || git fetch origin "$sha" \
      || git fetch --unshallow 2>/dev/null \
      || git fetch origin
    git checkout --detach "$sha"
    echo "✓ $path @ $(git rev-parse HEAD)"
    if [ "$(git rev-parse HEAD)" != "$sha" ]; then
      echo "ERROR: expected $sha, got $(git rev-parse HEAD)" >&2
      exit 1
    fi
  )
}

echo "Pinning DeepInfer vendors under $ROOT/vendor ..."
clone_at vendor/DeepInfer      https://github.com/deepseek-ai/DeepInfer.git      "$DEEPINFER_SHA"
clone_at vendor/DeepGEMM       https://github.com/deepseek-ai/DeepGEMM.git       "$DEEPGEMM_SHA"
clone_at vendor/FlashMLA       https://github.com/deepseek-ai/FlashMLA.git       "$FLASHMLA_SHA"
clone_at vendor/DeepEP         https://github.com/deepseek-ai/DeepEP.git         "$DEEPEP_SHA"
clone_at vendor/DeepSelect     https://github.com/deepseek-ai/DeepSelect.git     "$DEEPSELECT_SHA"
clone_at vendor/DeepGEMM-Ascend https://github.com/deepseek-ai/DeepGEMM-Ascend.git "$DEEPGEMM_ASCEND_SHA"
clone_at vendor/DeepEP-Ascend  https://github.com/deepseek-ai/DeepEP-Ascend.git  "$DEEPEP_ASCEND_SHA"

echo
echo "All pins verified. Next (local, when ready to commit gitlinks):"
echo "  git add vendor/DeepInfer vendor/DeepGEMM vendor/FlashMLA vendor/DeepEP \\"
echo "          vendor/DeepSelect vendor/DeepGEMM-Ascend vendor/DeepEP-Ascend"
echo "Install DeepInfer (GPU / CUDA 13 + SM100 required for kernels):"
echo "  pip install -r vendor/DeepInfer/requirements-nvidia.txt"
echo "  pip install -e vendor/DeepInfer"
