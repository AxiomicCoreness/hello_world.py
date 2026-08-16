"""
deepseek.api — async HTTP client + streaming + CI warning/ignore.

Env:
  DEEPSEEK_API_KEY  optional; if set, complete/stream use DeepSeek HTTP API
  DEEPSEEK_BASE_URL optional; default https://api.deepseek.com
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Deque, Dict, List, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

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
    _record("warning", msg, *args)


def ignore(msg: str, *args: Any) -> None:
    _record("ignore", msg, *args)


def get_events(limit: int = 50) -> List[Dict[str, Any]]:
    items = list(_events)
    return items[-limit:] if limit > 0 else items


def clear_events() -> None:
    _events.clear()


@dataclass
class AsyncDeepSeekClient:
    """Async chat client (httpx) with offline fallback + SSE streaming."""

    api_key: Optional[str] = field(default_factory=lambda: os.environ.get("DEEPSEEK_API_KEY"))
    base_url: str = field(
        default_factory=lambda: os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    model: str = "deepseek-chat"
    timeout: float = 60.0
    _client: Any = field(default=None, repr=False)

    @property
    def online(self) -> bool:
        return bool(self.api_key) and httpx is not None

    def status(self) -> Dict[str, Any]:
        return {
            "online": self.online,
            "httpx": httpx is not None,
            "base_url": self.base_url,
            "model": self.model,
            "events": len(_events),
        }

    async def _get_http(self) -> Any:
        if httpx is None:
            raise RuntimeError("httpx not installed")
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def complete(self, prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
        """Async chat completion; offline echo if no API key / no httpx."""
        if not self.api_key or httpx is None:
            text = f"[offline deepseek] {prompt[:500]}"
            _record("complete_offline", prompt[:120])
            return {"mode": "offline", "text": text, "model": self.model}

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            client = await self._get_http()
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            _record("complete_online", prompt[:120])
            return {"mode": "online", "text": text, "raw": data, "model": self.model}
        except Exception as e:
            warning(f"deepseek complete failed: {e}")
            return {"mode": "error", "text": str(e), "model": self.model, "error": type(e).__name__}

    async def stream(self, prompt: str, max_tokens: int = 256) -> AsyncIterator[str]:
        """Yield token/text chunks (SSE-friendly). Offline: word-chunk the echo."""
        if not self.api_key or httpx is None:
            text = f"[offline deepseek] {prompt[:500]}"
            _record("stream_offline", prompt[:120])
            for word in text.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
            return

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
        }
        try:
            client = await self._get_http()
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = (
                                data.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content")
                            )
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue
            _record("stream_online", prompt[:120])
        except Exception as e:
            warning(f"deepseek stream failed: {e}")
            yield f"[error:{type(e).__name__}] {e}"

    def complete_sync(self, prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            raise RuntimeError("use await complete() inside async code")
        return asyncio.run(self.complete(prompt, max_tokens=max_tokens))


DeepSeekClient = AsyncDeepSeekClient

_default_client: Optional[AsyncDeepSeekClient] = None


def get_client() -> AsyncDeepSeekClient:
    global _default_client
    if _default_client is None:
        _default_client = AsyncDeepSeekClient()
    return _default_client
