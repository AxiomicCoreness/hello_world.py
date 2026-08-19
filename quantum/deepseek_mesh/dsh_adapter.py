#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ quantum/deepseek_mesh/dsh_adapter.py
Soft bridge: official DeepSeek Harness SDK ↔ Garden offline echo.

Modes
  offline  — no key / no SDK; deterministic φ-tagged echo
  openai   — OpenAI-compatible HTTPS to DEEPSEEK_BASE_URL
  dsh      — deepseek_harness.DeepSeekHarness JSON-RPC runtime (optional)

Env
  DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DSH_MODEL, DEEPSEEK_MODEL
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHASE_LOCK_DEG = 202.6
ENTROPY_FLOOR = PHI ** -1418
DEFAULT_MODEL = os.environ.get("DSH_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat"
DEFAULT_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


@dataclass
class AdapterResult:
    mode: str
    text: str
    model: str
    coherence: float = 1.0
    phase_lock_deg: float = PHASE_LOCK_DEG
    latency_ms: float = 0.0
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def _garden_invariants() -> Dict[str, Any]:
    return {
        "coherence": 1.0,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "entropy_floor": float(ENTROPY_FLOOR) if ENTROPY_FLOOR != 0 else 0.0,
        "phi": PHI,
        "seal": "∀∞φ² · DSH_ADAPTER · WOOD_DRAGON_0.91 · SEALED",
    }


def offline_complete(prompt: str, model: str = DEFAULT_MODEL) -> AdapterResult:
    """Deterministic offline completion — no network."""
    t0 = time.time()
    body = (
        f"[GARDEN_OFFLINE_ECHO] model={model}\n"
        f"prompt_len={len(prompt)} coherence=1.0 phase={PHASE_LOCK_DEG}\n"
        f"echo: {prompt[:240]}"
    )
    return AdapterResult(
        mode="offline",
        text=body,
        model=model,
        latency_ms=(time.time() - t0) * 1000.0,
        meta=_garden_invariants(),
    )


def openai_compatible_complete(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 256,
    timeout: float = 60.0,
) -> AdapterResult:
    """HTTPS chat.completions against DeepSeek (or any OpenAI-compatible proxy)."""
    key = api_key or os.environ.get("DEEPSEEK_API_KEY") or ""
    base = (base_url or DEFAULT_BASE).rstrip("/")
    if not key:
        return offline_complete(prompt, model=model)

    t0 = time.time()
    try:
        import urllib.request

        url = f"{base}/v1/chat/completions" if not base.endswith("/v1") else f"{base}/chat/completions"
        if base.endswith("/v1") or "/v1/" in base:
            url = f"{base.rstrip('/')}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"
        payload = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return AdapterResult(
            mode="openai",
            text=text,
            model=model,
            latency_ms=(time.time() - t0) * 1000.0,
            meta={**_garden_invariants(), "usage": data.get("usage")},
        )
    except Exception as e:
        r = offline_complete(prompt, model=model)
        r.meta = {**(r.meta or {}), "fallback_reason": str(e)}
        return r


def dsh_sdk_available() -> bool:
    try:
        import deepseek_harness  # noqa: F401

        return True
    except Exception:
        return False


def dsh_complete(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    cwd: Optional[str] = None,
    session_root: Optional[str] = None,
    cordis: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> AdapterResult:
    """Run one turn via official deepseek_harness.DeepSeekHarness if installed."""
    t0 = time.time()
    try:
        from deepseek_harness import DeepSeekHarness

        kwargs: Dict[str, Any] = {
            "provider": "deepseek-official",
            "model": model,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if cwd:
            kwargs["cwd"] = cwd
        if session_root:
            kwargs["session_root"] = session_root
        if cordis:
            kwargs["cordis"] = cordis
        with DeepSeekHarness(**kwargs) as harness:
            result = harness.run(prompt)
        text = getattr(result, "final_response", None) or str(result)
        return AdapterResult(
            mode="dsh",
            text=text,
            model=model,
            latency_ms=(time.time() - t0) * 1000.0,
            meta=_garden_invariants(),
        )
    except Exception as e:
        r = offline_complete(prompt, model=model)
        r.meta = {**(r.meta or {}), "dsh_error": str(e)}
        return r


def complete(prompt: str, prefer: str = "auto", **kwargs: Any) -> AdapterResult:
    """
    prefer: auto | offline | openai | dsh
      auto → dsh if SDK+key, else openai if key, else offline
    """
    prefer = (prefer or "auto").lower()
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    if prefer == "offline":
        return offline_complete(prompt, model=kwargs.get("model", DEFAULT_MODEL))
    if prefer == "dsh":
        return dsh_complete(prompt, **{k: v for k, v in kwargs.items() if k in ("model", "cwd", "session_root", "cordis", "max_tokens")})
    if prefer == "openai":
        return openai_compatible_complete(prompt, **{k: v for k, v in kwargs.items() if k in ("api_key", "base_url", "model", "max_tokens", "timeout")})
    # auto
    if dsh_sdk_available() and key:
        return dsh_complete(prompt, model=kwargs.get("model", DEFAULT_MODEL))
    if key:
        return openai_compatible_complete(prompt, model=kwargs.get("model", DEFAULT_MODEL))
    return offline_complete(prompt, model=kwargs.get("model", DEFAULT_MODEL))


def probe() -> Dict[str, Any]:
    """Harness-friendly status (no network required)."""
    return {
        "dsh_sdk": dsh_sdk_available(),
        "api_key_set": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "base_url": DEFAULT_BASE,
        "model": DEFAULT_MODEL,
        "invariants": _garden_invariants(),
        "modes": ["offline", "openai", "dsh"],
    }
