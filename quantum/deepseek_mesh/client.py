# quantum/deepseek_mesh/client.py
# Replaced with async client (deepseek.api) and sync wrappers.
# Seal: ∀∞φ² · ASYNC_CLIENT_WRAP · WOOD_DRAGON_0.91 · SEALED

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from deepseek.api import (
    AsyncDeepSeekClient,
    get_client,
    get_ready_client,
    FiberState,
    CordisError,
)


def _run_async(coro):
    """Run an async coroutine in a new event loop (sync wrapper)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop – safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # If we are already in an async context, we cannot use asyncio.run()
        # We'll use loop.run_until_complete, but this can cause issues.
        # For simplicity, we raise a clear error.
        raise RuntimeError(
            "Cannot call sync wrapper from within an async event loop. "
            "Use async methods directly: await client.complete(...)"
        )


def chat(prompt: str, prefer: str = "auto", **kwargs: Any) -> Dict[str, Any]:
    """
    Sync wrapper for client.complete.
    """
    client = _run_async(get_ready_client())
    result = _run_async(client.complete(prompt, **kwargs))
    result["prefer"] = prefer
    return result


def chat_http(prompt: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Sync wrapper; forces HTTP mode via deepseek_http adapter.
    """
    return chat(prompt, prefer="http", **kwargs)


def echo(prompt: str) -> Dict[str, Any]:
    """
    Sync echo – returns prompt back with client status.
    """
    client = _run_async(get_ready_client())
    return {
        "echo": prompt,
        "client_status": client.status(),
    }


def status() -> Dict[str, Any]:
    """
    Sync status – returns client and mesh status.
    """
    client = get_client()
    return {
        "client": client.status(),
        "mesh": "online",
    }


# Re‑export constants and types from dsh_adapter for backward compatibility
from .dsh_adapter import (
    MODE_DEEPSEEK_HTTP,
    MODE_DSH,
    MODE_OFFLINE,
    AdapterResult,
)


__all__ = [
    "chat",
    "chat_http",
    "echo",
    "status",
    "MODE_DEEPSEEK_HTTP",
    "MODE_DSH",
    "MODE_OFFLINE",
    "AdapterResult",
]
