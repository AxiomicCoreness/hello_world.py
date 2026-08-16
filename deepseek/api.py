"""
deepseek.api — functional local client + CI-compatible warning/ignore.

Env:
  DEEPSEEK_API_KEY  optional; if set, complete() posts to DeepSeek HTTP API
  DEEPSEEK_BASE_URL optional; default https://api.deepseek.com
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

_MAX_EVENTS = 256
_events: Deque[Dict[str, Any]] = deque(maxlen=_MAX_EVENTS)


def _record(kind: str, msg: str, *args: Any) -> None:
    _events.append(
        {
            "ts": time.time(),
            "kind": kind,
            "msg": msg,
            "args": [repr(a) for a in args],
        }
    )


def warning(msg: str, *args: Any) -> None:
    """Record a warning event (CI + runtime)."""
    _record("warning", msg, *args)


def ignore(msg: str, *args: Any) -> None:
    """Record an ignore/info event (used by CI route-count check)."""
    _record("ignore", msg, *args)


def get_events(limit: int = 50) -> List[Dict[str, Any]]:
    items = list(_events)
    if limit > 0:
        return items[-limit:]
    return items


def clear_events() -> None:
    _events.clear()


@dataclass
class DeepSeekClient:
    """Minimal chat/complete client with offline fallback."""

    api_key: Optional[str] = field(default_factory=lambda: os.environ.get("DEEPSEEK_API_KEY"))
    base_url: str = field(
        default_factory=lambda: os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    model: str = "deepseek-chat"

    @property
    def online(self) -> bool:
        return bool(self.api_key)

    def status(self) -> Dict[str, Any]:
        return {
            "online": self.online,
            "base_url": self.base_url,
            "model": self.model,
            "events": len(_events),
        }

    def complete(self, prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
        """Chat completion; falls back to local echo if no API key."""
        if not self.api_key:
            text = f"[offline deepseek] {prompt[:500]}"
            _record("complete_offline", prompt[:120])
            return {"mode": "offline", "text": text, "model": self.model}

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            _record("complete_online", prompt[:120])
            return {"mode": "online", "text": text, "raw": data, "model": self.model}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            warning(f"deepseek complete failed: {e}")
            return {"mode": "error", "text": str(e), "model": self.model}


def get_client() -> DeepSeekClient:
    return DeepSeekClient()
