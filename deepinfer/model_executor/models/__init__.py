# --- AxiomicCoreness repo header (not upstream) ---
# Sparse vendor of deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9 (Apache-2.0, see deepinfer/LICENSE).
# The former comment-only repo stub is preserved verbatim in deepinfer/PROVENANCE.md; it was
# replaced because deepinfer/hugging_face/config.py (in the v4_modules import closure) needs
# ModelRegistry from here. Every byte after the marker line below is identical to upstream
# deepinfer/model_executor/models/__init__.py (blob sha in deepinfer/VENDOR_MANIFEST.json).
# Note: ModelRegistry resolves "deepseek_vl" lazily; deepseek_vl.py is NOT vendored (see PROVENANCE.md).
# --- end repo header; upstream deepinfer/model_executor/models/__init__.py follows byte-for-byte ---
# SPDX-License-Identifier: Apache-2.0
# Derived from vLLM; modified by DeepSeek.

from __future__ import annotations

import importlib

import torch.nn as nn

from deepinfer.logger import init_logger

logger = init_logger(__name__)

# Architecture -> (module, class).
_MODELS = {
    "DeepseekV41ForCausalLM": ("deepseek_vl", "DeepseekVLForCausalLM"),
}


class ModelRegistry:
    @staticmethod
    def load_model_cls(model_arch: str) -> type[nn.Module] | None:
        if model_arch not in _MODELS:
            return None

        module_name, model_cls_name = _MODELS[model_arch]
        module = importlib.import_module(f"deepinfer.model_executor.models.{module_name}")
        return getattr(module, model_cls_name, None)

    @staticmethod
    def get_supported_archs() -> list[str]:
        return list(_MODELS.keys())


__all__ = [
    "ModelRegistry",
]
