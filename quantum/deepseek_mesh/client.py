# DeepSeek Client — Entry 8845 / harness lattice integration
# Formerly: orchestrator/deepseek_client.py

"""
DeepSeek API client for external model integration.
Injects Garden invariants: coherence=1.0, phase=202.6, entropy=φ⁻¹⁴¹⁸
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .dsh_adapter import (
    MODE_DEEPSEEK_HTTP,
    MODE_DSH,
    MODE_OFFLINE,
    complete,
    offline_complete,
    probe,
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", os.getenv("DSH_MODEL", "deepseek-chat"))


def chat(prompt: str, prefer: str = "auto", **kwargs: Any) -> Dict[str, Any]:
    return complete(
        prompt,
        prefer=prefer,
        model=kwargs.get("model", DEEPSEEK_MODEL),
        **{k: v for k, v in kwargs.items() if k != "model"},
    ).to_dict()


def status() -> Dict[str, Any]:
    return probe()


def echo(prompt: str) -> Dict[str, Any]:
    return offline_complete(prompt, model=DEEPSEEK_MODEL).to_dict()


def chat_http(prompt: str, **kwargs: Any) -> Dict[str, Any]:
    """Explicit deepseek_http path."""
    return chat(prompt, prefer=MODE_DEEPSEEK_HTTP, **kwargs)
