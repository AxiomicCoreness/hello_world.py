"""
deepseek.api — async client with Cordis-style fiber lifecycle +
Garden dsh_adapter bridge for harness lattice.

FiberState mirrors cordiverse Cordis:
  PENDING → LOADING → ACTIVE
                   ↘ FAILED
  ACTIVE  → UNLOADING → DISPOSED | PENDING

Offline (no API key / no httpx) is a first-class ACTIVE local mode.
Module-level complete_sync routes through quantum.deepseek_mesh.dsh_adapter
when available (official SDK | OpenAI-compatible | offline echo).

Env:
  DEEPSEEK_API_KEY   optional
  DEEPSEEK_BASE_URL  default https://api.deepseek.com
  DSH_MODEL / DEEPSEEK_MODEL
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Deque, Dict, List, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

_MAX_EVENTS = 256
_events: Deque[Dict[str, Any]] = deque(maxlen=_MAX_EVENTS)


class FiberState(str, Enum):
    PENDING = "PENDING"
    LOADING = "LOADING"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    UNLOADING = "UNLOADING"
    DISPOSED = "DISPOSED"


class CordisError(RuntimeError):
    """Stable coded error (Cordis-compatible shape)."""

    INACTIVE_EFFECT = "INACTIVE_EFFECT"
    NOT_READY = "NOT_READY"
    DISPOSED = "DISPOSED"

    def __init__(self, code: str, message: Optional[str] = None):
        self.code = code
        super().__init__(message or code)


def _record(kind: str, msg: str, *args: Any) -> None:
    _events.append(
        {"ts": time.time(), "kind": kind, "msg": msg, "args": [repr(a) for a in args]}
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


def complete_sync(prompt: str, max_tokens: int = 64, prefer: str = "auto") -> Dict[str, Any]:
    """Harness / test_all entry — prefers dsh_adapter lattice."""
    try:
        from quantum.deepseek_mesh.dsh_adapter import complete

        r = complete(prompt, prefer=prefer, max_tokens=max_tokens)
        _record("complete_sync_adapter", r.mode)
        return r.to_dict()
    except Exception as e:
        _record("complete_sync_fallback", str(e))
        return {
            "mode": "offline",
            "text": f"[offline deepseek] {prompt[:500]}",
            "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            "error": str(e),
        }


@dataclass
class AsyncDeepSeekClient:
    """DeepSeek fiber: lifecycle + complete/stream."""

    api_key: Optional[str] = field(default_factory=lambda: os.environ.get("DEEPSEEK_API_KEY"))
    base_url: str = field(
        default_factory=lambda: os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    model: str = field(
        default_factory=lambda: os.environ.get("DSH_MODEL")
        or os.environ.get("DEEPSEEK_MODEL")
        or "deepseek-chat"
    )
    timeout: float = 60.0

    _client: Any = field(default=None, repr=False)
    _uid: Optional[int] = field(default=0, repr=False)
    _state: FiberState = field(default=FiberState.PENDING, repr=False)
    _error: Optional[BaseException] = field(default=None, repr=False)
    _inertia: Optional[asyncio.Task] = field(default=None, repr=False)
    _mode: str = field(default="offline", repr=False)

    @property
    def state(self) -> FiberState:
        if self._uid is None:
            return FiberState.DISPOSED
        if self._state in (FiberState.LOADING, FiberState.UNLOADING):
            return self._state
        if self._error is not None:
            return FiberState.FAILED
        return self._state

    @property
    def online(self) -> bool:
        return self._mode == "online" and self.state == FiberState.ACTIVE

    def assert_active(self) -> None:
        if self._uid is None:
            raise CordisError(CordisError.INACTIVE_EFFECT, "cannot use disposed deepseek fiber")
        if self.state == FiberState.DISPOSED:
            raise CordisError(CordisError.DISPOSED)

    async def await_ready(self) -> "AsyncDeepSeekClient":
        while self._inertia is not None and not self._inertia.done():
            await self._inertia
        if self._error is not None and self.state == FiberState.FAILED:
            raise self._error
        return self

    async def reload(self) -> FiberState:
        if self._uid is None:
            raise CordisError(CordisError.DISPOSED, "cannot reload disposed fiber")
        if self._inertia and not self._inertia.done():
            await self._inertia

        self._state = FiberState.LOADING
        self._error = None
        _record("fiber_loading", self.base_url)

        async def _do() -> None:
            try:
                if self.api_key and httpx is not None:
                    if self._client is None:
                        self._client = httpx.AsyncClient(timeout=self.timeout)
                    self._mode = "online"
                else:
                    self._mode = "offline"
                    if self._client is not None:
                        await self._client.aclose()
                        self._client = None
                self._state = FiberState.ACTIVE
                _record("fiber_active", self._mode)
            except Exception as e:
                self._error = e
                self._state = FiberState.FAILED
                warning(f"deepseek fiber FAILED: {e}")
            finally:
                self._inertia = None

        self._inertia = asyncio.create_task(_do())
        await self._inertia
        return self.state

    async def unload(self) -> FiberState:
        if self._uid is None:
            return FiberState.DISPOSED
        if self._inertia and not self._inertia.done():
            await self._inertia

        self._state = FiberState.UNLOADING
        _record("fiber_unloading", self._mode)

        async def _do() -> None:
            try:
                if self._client is not None:
                    await self._client.aclose()
                    self._client = None
            except Exception as e:
                warning(f"unload http close: {e}")
            finally:
                self._mode = "offline"
                self._state = FiberState.PENDING
                self._inertia = None
                _record("fiber_pending", "unloaded")

        self._inertia = asyncio.create_task(_do())
        await self._inertia
        return self.state

    async def dispose(self) -> None:
        await self.unload()
        self._uid = None
        self._state = FiberState.DISPOSED
        self._error = None
        _record("fiber_disposed", "uid=null")

    def status(self) -> Dict[str, Any]:
        return {
            "fiber": self.state.value,
            "mode": self._mode,
            "online": self.online,
            "httpx": httpx is not None,
            "has_key": bool(self.api_key),
            "base_url": self.base_url,
            "model": self.model,
            "events": len(_events),
            "last_error": str(self._error) if self._error else None,
        }

    async def _ensure_active(self) -> None:
        self.assert_active()
        if self.state == FiberState.PENDING:
            await self.reload()
        if self.state == FiberState.FAILED:
            await self.reload()
        if self.state != FiberState.ACTIVE:
            raise CordisError(
                CordisError.NOT_READY,
                f"deepseek fiber not ACTIVE (state={self.state.value})",
            )

    async def complete(self, prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
        # Prefer lattice adapter for unified offline/openai/dsh behaviour
        try:
            from quantum.deepseek_mesh.dsh_adapter import complete as lattice_complete

            r = lattice_complete(prompt, prefer="auto", max_tokens=max_tokens, model=self.model)
            _record("complete_lattice", r.mode)
            return r.to_dict()
        except Exception:
            pass

        try:
            await self._ensure_active()
        except CordisError as e:
            return {"mode": "error", "text": str(e), "error": e.code, "fiber": self.state.value}

        if self._mode == "offline":
            text = f"[offline deepseek] {prompt[:500]}"
            _record("complete_offline", prompt[:120])
            return {"mode": "offline", "text": text, "model": self.model, "fiber": FiberState.ACTIVE.value}

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
            assert self._client is not None
            resp = await self._client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            _record("complete_online", prompt[:120])
            return {"mode": "online", "text": text, "raw": data, "model": self.model, "fiber": FiberState.ACTIVE.value}
        except Exception as e:
            self._error = e
            self._state = FiberState.FAILED
            warning(f"deepseek complete failed: {e}")
            return {
                "mode": "error",
                "text": str(e),
                "model": self.model,
                "error": type(e).__name__,
                "fiber": FiberState.FAILED.value,
            }

    async def stream(self, prompt: str, max_tokens: int = 256) -> AsyncIterator[str]:
        try:
            await self._ensure_active()
        except CordisError as e:
            yield f"[error:{e.code}] {e}"
            return

        if self._mode == "offline":
            text = f"[offline deepseek] {prompt[:500]}"
            _record("stream_offline", prompt[:120])
            for word in text.split(" "):
                yield word + " "
                await asyncio.sleep(0.005)
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
            assert self._client is not None
            async with self._client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
            _record("stream_online", prompt[:120])
        except Exception as e:
            self._error = e
            self._state = FiberState.FAILED
            warning(f"deepseek stream failed: {e}")
            yield f"[error:{type(e).__name__}] {e}"

    def complete_sync(self, prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
        return complete_sync(prompt, max_tokens=max_tokens)


DeepSeekClient = AsyncDeepSeekClient

_default_client: Optional[AsyncDeepSeekClient] = None


def get_client() -> AsyncDeepSeekClient:
    global _default_client
    if _default_client is None or _default_client.state == FiberState.DISPOSED:
        _default_client = AsyncDeepSeekClient()
    return _default_client


async def get_ready_client() -> AsyncDeepSeekClient:
    c = get_client()
    if c.state in (FiberState.PENDING, FiberState.FAILED):
        await c.reload()
    await c.await_ready()
    return c
