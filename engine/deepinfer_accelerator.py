# SPDX-License-Identifier: Apache-2.0
"""Optional DeepInfer accelerator under sovereign / personal engines.

Control plane stays: garden_surgery, sovereign_engine*, deepseek.api, quantum.
DeepInfer is loaded only when the package is installed (vendor/DeepInfer +
kernels). No torch.set_default_dtype hijack. No stub LLMEngine.

Usage:
    from engine.deepinfer_accelerator import complete, deepinfer_available
    result = complete("hello")  # falls back to deepseek.api if DeepInfer absent
"""
from __future__ import annotations

import importlib
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_DEEPINFER_IMPORT_ERROR: BaseException | None = None


def deepinfer_available() -> bool:
    """True when the real ``deepinfer`` package imports cleanly."""
    return _try_import_deepinfer() is not None


def _try_import_deepinfer() -> Any | None:
    global _DEEPINFER_IMPORT_ERROR
    try:
        return importlib.import_module("deepinfer")
    except Exception as exc:  # noqa: BLE001 — optional dependency
        _DEEPINFER_IMPORT_ERROR = exc
        return None


def deepinfer_status() -> dict[str, Any]:
    """Diagnostic blob for harness / health endpoints (no side effects)."""
    mod = _try_import_deepinfer()
    return {
        "available": mod is not None,
        "accelerator_env": os.environ.get("DEEPINFER_ACCELERATOR"),
        "import_error": (
            None
            if mod is not None
            else f"{type(_DEEPINFER_IMPORT_ERROR).__name__}: {_DEEPINFER_IMPORT_ERROR}"
            if _DEEPINFER_IMPORT_ERROR
            else None
        ),
        "role": "optional_accelerator",
        "primary_engines": (
            "garden_surgery",
            "sovereign_engine",
            "deepseek.api",
            "quantum",
        ),
    }


def complete(
    prompt: str,
    *,
    max_tokens: int = 64,
    prefer: str = "auto",
) -> dict[str, Any]:
    """Generate text.

    Order:
      1. If ``DEEPINFER_FORCE=1`` and DeepInfer is importable, use offline
         DeepInfer path when a model dir is configured (else report needs_model).
      2. Otherwise always prefer ``deepseek.api.complete_sync`` (sovereign path).
      3. Last resort: local offline echo.

    DeepInfer is never the default when personal engines work.
    """
    force = os.environ.get("DEEPINFER_FORCE", "").strip() in ("1", "true", "yes")
    if force and deepinfer_available():
        di = _complete_via_deepinfer(prompt, max_tokens=max_tokens)
        if di is not None:
            return di

    # Primary: personal / sovereign DeepSeek fiber
    try:
        from deepseek.api import complete_sync

        out = complete_sync(prompt, max_tokens=max_tokens, prefer=prefer)
        if isinstance(out, dict):
            out = dict(out)
            out.setdefault("backend", "deepseek.api")
            out["deepinfer"] = deepinfer_status()
            return out
    except Exception as exc:  # noqa: BLE001
        logger.info("deepseek.api fallback failed: %s", exc)

    if deepinfer_available():
        di = _complete_via_deepinfer(prompt, max_tokens=max_tokens)
        if di is not None:
            return di

    return {
        "mode": "offline",
        "backend": "echo",
        "text": f"[offline accelerator] {prompt[:500]}",
        "deepinfer": deepinfer_status(),
    }


def _complete_via_deepinfer(prompt: str, *, max_tokens: int) -> dict[str, Any] | None:
    """Best-effort offline DeepInfer call without constructing a paste stub engine.

    Real offline inference needs a checkpoint and GPU stack. We only probe the
    package and report configuration; callers keep using deepseek.api for text
    until a model path is wired.
    """
    model_dir = os.environ.get("DEEPINFER_HF_MODEL_DIR") or os.environ.get(
        "DEEPINFER_MODEL"
    )
    status = deepinfer_status()
    if not model_dir:
        return {
            "mode": "deepinfer_probe",
            "backend": "deepinfer",
            "text": "",
            "needs_model": True,
            "hint": "Set DEEPINFER_HF_MODEL_DIR to a DeepSeek-V4.1-Flash checkpoint",
            "deepinfer": status,
            "max_tokens": max_tokens,
            "prompt_preview": prompt[:120],
        }
    # Full LLMEngine construction requires CUDA/SM100 + built _C extensions.
    # Refuse to invent a stub; surface readiness only.
    return {
        "mode": "deepinfer_configured",
        "backend": "deepinfer",
        "text": "",
        "needs_runtime": True,
        "model_dir": model_dir,
        "hint": (
            "Package present and model dir set; run vendor/DeepInfer examples/"
            "offline_inference.py on SM100+CUDA13 hardware, or keep deepseek.api"
        ),
        "deepinfer": status,
        "max_tokens": max_tokens,
        "prompt_preview": prompt[:120],
    }


__all__ = [
    "complete",
    "deepinfer_available",
    "deepinfer_status",
]
