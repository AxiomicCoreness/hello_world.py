"""Loopback-only bind policy for Dual ASGI."""

from __future__ import annotations

BIND_HOST = "127.0.0.1"
BIND_PORT = 8024
REFUSED_HOSTS = frozenset({"0.0.0.0", "::", "[::]"})


def resolve(host: str | None = None, port: int | None = None) -> tuple[str, int]:
    h = BIND_HOST if host is None else str(host)
    p = BIND_PORT if port is None else int(port)
    if h in REFUSED_HOSTS:
        raise ValueError("refuse 0.0.0.0 / wildcard — Dual ASGI is 127.0.0.1:8024")
    if p != BIND_PORT:
        raise ValueError("Dual ASGI port is 8024")
    return h, p


def uvicorn_argv(module: str = "fastMCP.gearbox:app") -> list[str]:
    host, port = resolve()
    return ["uvicorn", module, "--host", host, "--port", str(port)]
