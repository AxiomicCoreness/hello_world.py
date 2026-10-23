"""K8s liveness/readiness probes — no IRC sockets."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "sovereign-irc-bridge",
        "irc_host_label": "irc.abjects.net",
        "live_irc": False,
    }
