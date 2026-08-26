"""OpenAI-compatible HTTP wrappers (Grok / DeepSeek / Mistral) via httpx.
API keys are read from the environment and never logged.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

PROVIDERS = {
    "grok": {
        "base": os.getenv("GROK_BASE_URL", "https://api.x.ai/v1"),
        "key_env": "XAI_API_KEY",
        "model": os.getenv("GROK_MODEL", "grok-3"),
    },
    "deepseek": {
        "base": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "key_env": "DEEPSEEK_API_KEY",
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    },
    "mistral": {
        "base": os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
        "key_env": "MISTRAL_API_KEY",
        "model": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
    },
}


def provider_status() -> Dict[str, Any]:
    out = {}
    for name, cfg in PROVIDERS.items():
        out[name] = {
            "configured": bool(os.getenv(cfg["key_env"])),
            "base": cfg["base"],
            "model": cfg["model"],
            "key_env": cfg["key_env"],
        }
    return out


def chat(provider: str, messages: List[Dict[str, str]], model: Optional[str] = None) -> Dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider: {provider}")
    cfg = PROVIDERS[provider]
    key = os.getenv(cfg["key_env"], "")
    if not key:
        return {"ok": False, "provider": provider, "error": f"{cfg['key_env']} not set"}
    url = cfg["base"].rstrip("/") + "/chat/completions"
    payload = {"model": model or cfg["model"], "messages": messages}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return {"ok": False, "provider": provider, "error": type(e).__name__}
    choice = (data.get("choices") or [{}])[0]
    text = ((choice.get("message") or {}).get("content")) or ""
    return {"ok": True, "provider": provider, "model": payload["model"], "text_len": len(text)}
