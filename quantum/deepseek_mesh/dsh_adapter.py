#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌀∀ quantum/deepseek_mesh/dsh_adapter.py
DeepSeek-only lattice adapter.

Modes
  offline         — no key; deterministic φ-tagged echo
  deepseek_http   — HTTPS chat.completions → DEEPSEEK_BASE_URL
  dsh             — deepseek_harness.DeepSeekHarness (optional SDK)

Streaming (NDJSON)
  complete_stream() / CLI --stream emit one JSON object per line:
    {"event": "start", ...}
    {"event": "delta", "text": "..."}
    {"event": "complete", "mode": "...", "text": "...", "latency_ms": ...}

Env
  DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DSH_MODEL, DEEPSEEK_MODEL

Seal: ∀∞φ² · DEEPSEEK_NDJSON_8925 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Generator, Iterable, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHASE_LOCK_DEG = 202.6
ENTROPY_FLOOR = PHI ** -1418
DEFAULT_MODEL = os.environ.get("DSH_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat"
DEFAULT_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
SEAL_CORE = "∀∞φ² · DEEPSEEK_NDJSON_8925 · WOOD_DRAGON_0.91 · SEALED"

MODE_OFFLINE = "offline"
MODE_DEEPSEEK_HTTP = "deepseek_http"
MODE_DSH = "dsh"


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
        return asdict(self)


def _garden_invariants() -> Dict[str, Any]:
    return {
        "coherence": 1.0,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "entropy_floor": float(ENTROPY_FLOOR) if ENTROPY_FLOOR != 0 else 0.0,
        "phi": PHI,
        "seal": SEAL_CORE,
    }


def _emit(obj: Dict[str, Any]) -> None:
    """Write one NDJSON line and flush (CI / live logs)."""
    sys.stdout.write(json.dumps(obj, default=str) + "\n")
    sys.stdout.flush()


def offline_complete(prompt: str, model: str = DEFAULT_MODEL) -> AdapterResult:
    """Deterministic offline completion — no network."""
    t0 = time.time()
    body = (
        f"[GARDEN_OFFLINE_ECHO] model={model}\n"
        f"prompt_len={len(prompt)} coherence=1.0 phase={PHASE_LOCK_DEG}\n"
        f"echo: {prompt[:240]}"
    )
    return AdapterResult(
        mode=MODE_OFFLINE,
        text=body,
        model=model,
        latency_ms=(time.time() - t0) * 1000.0,
        meta=_garden_invariants(),
    )


def deepseek_http_complete(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 256,
    timeout: float = 60.0,
) -> AdapterResult:
    """HTTPS chat.completions against DeepSeek official API only."""
    key = api_key or os.environ.get("DEEPSEEK_API_KEY") or ""
    base = (base_url or DEFAULT_BASE).rstrip("/")
    if not key:
        return offline_complete(prompt, model=model)

    t0 = time.time()
    try:
        import urllib.request

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
            mode=MODE_DEEPSEEK_HTTP,
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
    """One turn via official deepseek_harness.DeepSeekHarness if installed."""
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
            mode=MODE_DSH,
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
    prefer: auto | offline | deepseek_http | deepseek | dsh
      auto → dsh if SDK+key, else deepseek_http if key, else offline
    """
    prefer = (prefer or "auto").lower()
    if prefer in ("openai", "chatgpt", "anthropic", "claude", "grok", "deepseek"):
        prefer = MODE_DEEPSEEK_HTTP

    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    model = kwargs.get("model", DEFAULT_MODEL)

    if prefer == MODE_OFFLINE:
        return offline_complete(prompt, model=model)
    if prefer == MODE_DSH:
        return dsh_complete(
            prompt,
            **{
                k: v
                for k, v in kwargs.items()
                if k in ("model", "cwd", "session_root", "cordis", "max_tokens")
            },
        )
    if prefer == MODE_DEEPSEEK_HTTP:
        return deepseek_http_complete(
            prompt,
            **{
                k: v
                for k, v in kwargs.items()
                if k in ("api_key", "base_url", "model", "max_tokens", "timeout")
            },
        )
    if dsh_sdk_available() and key:
        return dsh_complete(prompt, model=model)
    if key:
        return deepseek_http_complete(prompt, model=model)
    return offline_complete(prompt, model=model)


def probe() -> Dict[str, Any]:
    """Harness-friendly status (no network required)."""
    return {
        "dsh_sdk": dsh_sdk_available(),
        "api_key_set": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "base_url": DEFAULT_BASE,
        "model": DEFAULT_MODEL,
        "invariants": _garden_invariants(),
        "modes": [MODE_OFFLINE, MODE_DEEPSEEK_HTTP, MODE_DSH],
        "stream": "NDJSON",
        "seal": SEAL_CORE,
    }


# ── NDJSON streaming ──

def _chunk_text(text: str, size: int = 48) -> List[str]:
    if not text:
        return [""]
    return [text[i : i + size] for i in range(0, len(text), size)]


def offline_stream(
    prompt: str, model: str = DEFAULT_MODEL, chunk_size: int = 48
) -> Generator[Dict[str, Any], None, None]:
    """Deterministic NDJSON stream (CI-safe, no network)."""
    t0 = time.time()
    yield {
        "event": "start",
        "mode": MODE_OFFLINE,
        "model": model,
        "prompt_len": len(prompt),
        "seal": SEAL_CORE,
    }
    result = offline_complete(prompt, model=model)
    for piece in _chunk_text(result.text, chunk_size):
        yield {"event": "delta", "text": piece}
    yield {
        "event": "complete",
        "mode": MODE_OFFLINE,
        "model": model,
        "text": result.text,
        "latency_ms": (time.time() - t0) * 1000.0,
        "coherence": 1.0,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "seal": SEAL_CORE,
    }


def deepseek_http_stream(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 256,
    timeout: float = 60.0,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream chat.completions (stream=true) as NDJSON.
    Falls back to offline_stream if no key or on error.
    """
    key = api_key or os.environ.get("DEEPSEEK_API_KEY") or ""
    if not key:
        yield from offline_stream(prompt, model=model)
        return

    base = (base_url or DEFAULT_BASE).rstrip("/")
    if base.endswith("/v1") or "/v1/" in base:
        url = f"{base.rstrip('/')}/chat/completions"
    else:
        url = f"{base}/v1/chat/completions"

    t0 = time.time()
    yield {
        "event": "start",
        "mode": MODE_DEEPSEEK_HTTP,
        "model": model,
        "prompt_len": len(prompt),
        "seal": SEAL_CORE,
    }

    parts: List[str] = []
    try:
        import urllib.request

        payload = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "stream": True,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "Accept": "text/event-stream",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            while True:
                raw = resp.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content") or ""
                    if piece:
                        parts.append(piece)
                        yield {"event": "delta", "text": piece}
        full = "".join(parts)
        yield {
            "event": "complete",
            "mode": MODE_DEEPSEEK_HTTP,
            "model": model,
            "text": full,
            "latency_ms": (time.time() - t0) * 1000.0,
            "coherence": 1.0,
            "phase_lock_deg": PHASE_LOCK_DEG,
            "seal": SEAL_CORE,
        }
    except Exception as e:
        # Fallback: offline stream remainder (already emitted start)
        result = offline_complete(prompt, model=model)
        for piece in _chunk_text(result.text, 48):
            yield {"event": "delta", "text": piece}
        yield {
            "event": "complete",
            "mode": MODE_OFFLINE,
            "model": model,
            "text": result.text,
            "latency_ms": (time.time() - t0) * 1000.0,
            "fallback_reason": str(e),
            "coherence": 1.0,
            "phase_lock_deg": PHASE_LOCK_DEG,
            "seal": SEAL_CORE,
        }


def complete_stream(
    prompt: str, prefer: str = "auto", **kwargs: Any
) -> Generator[Dict[str, Any], None, None]:
    """
    NDJSON event generator.
    prefer: auto | offline | deepseek_http
    """
    prefer = (prefer or "auto").lower()
    if prefer in ("openai", "chatgpt", "anthropic", "claude", "grok", "deepseek"):
        prefer = MODE_DEEPSEEK_HTTP
    model = kwargs.get("model", DEFAULT_MODEL)
    key = os.environ.get("DEEPSEEK_API_KEY") or ""

    if prefer == MODE_OFFLINE or (prefer == "auto" and not key):
        yield from offline_stream(prompt, model=model)
        return
    if prefer in (MODE_DEEPSEEK_HTTP, "auto"):
        yield from deepseek_http_stream(
            prompt,
            model=model,
            max_tokens=int(kwargs.get("max_tokens", 256)),
            timeout=float(kwargs.get("timeout", 60.0)),
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
        )
        return
    # dsh has no native stream — offline synthetic
    yield from offline_stream(prompt, model=model)


def run_stream_to_stdout(
    prompt: str, prefer: str = "offline", **kwargs: Any
) -> Dict[str, Any]:
    """Consume complete_stream and print NDJSON lines; return final complete event."""
    final: Dict[str, Any] = {}
    for ev in complete_stream(prompt, prefer=prefer, **kwargs):
        _emit(ev)
        if ev.get("event") == "complete":
            final = ev
    return final


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="DeepSeek mesh adapter")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--complete", action="store_true", help="One-shot complete")
    parser.add_argument(
        "--stream", action="store_true", help="NDJSON stream (start/delta/complete)"
    )
    parser.add_argument("--prompt", type=str, default="ci ping")
    parser.add_argument(
        "--prefer",
        type=str,
        default="offline",
        choices=["auto", "offline", "deepseek_http", "dsh"],
    )
    args = parser.parse_args()

    if args.probe:
        print(json.dumps(probe(), indent=2))
        return
    if args.stream:
        run_stream_to_stdout(args.prompt, prefer=args.prefer)
        return
    if args.complete:
        r = complete(args.prompt, prefer=args.prefer)
        print(json.dumps(r.to_dict(), indent=2))
        return
    print(json.dumps(probe(), indent=2))


if __name__ == "__main__":
    main()
