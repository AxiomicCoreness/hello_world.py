# SPDX-License-Identifier: Apache-2.0
# Derived from vLLM; modified by DeepSeek.

from __future__ import annotations

from pathlib import Path
from typing import Any

# --- Safe Imports for CI ---
try:
    from deepinfer import AttrDict
except ImportError:
    # Fallback for CI environments without the compiled DeepInfer module
    class AttrDict(dict):
        """A dictionary that allows attribute-style access."""
        def __getattr__(self, key: str) -> Any:
            try:
                return self[key]
            except KeyError:
                raise AttributeError(f"'AttrDict' object has no attribute '{key}'")

        def __setattr__(self, key: str, value: Any) -> None:
            self[key] = value

        def __delattr__(self, key: str) -> None:
            try:
                del self[key]
            except KeyError:
                raise AttributeError(f"'AttrDict' object has no attribute '{key}'")


def load_model_config(model: str) -> AttrDict:
    """加载 V4.1 的 model_cfg（AttrDict）。

    `model` 必须指向 HF 目录；配置与权重来自同一目录。

    返回的 model_cfg 至少包含：
    - model_cfg.architecture：HF architectures 中声明且通过注册表校验的架构名
    - model_cfg.gpt：模型结构（num_attention_heads / hidden_size / vocab_size / kv_lora_rank ...）
    - model_cfg.vl_aligner：必需的 HF 视觉/投影结构
    """
    try:
        # HF 配置解析只处理数据，不导入模型实现。
        from deepinfer.hugging_face import load_hf_model_config
    except ImportError:
        # Fallback for CI: Read config.json directly into an AttrDict
        import json
        config_path = Path(model) / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"HF config not found at {config_path}")
            
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        model_cfg = AttrDict(data)
        if "vl_aligner" not in model_cfg:
            raise AssertionError("Only multimodal HF models with vl_aligner are supported")
        return model_cfg

    # Native DeepInfer path
    model_cfg = load_hf_model_config(Path(model) / "config.json")
    assert "vl_aligner" in model_cfg, "Only multimodal HF models with vl_aligner are supported"
    return model_cfg
