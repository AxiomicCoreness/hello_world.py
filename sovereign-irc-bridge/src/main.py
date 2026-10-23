"""FastAPI entry: health + WebSocket stub; serves TeaVM debug-oracle static assets."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .api.health import router as health_router
from .bridge.ws_tcp_proxy import WsTcpProxyStub
from .models.settings import get_settings

logger = logging.getLogger("sovereign-irc-bridge")

app = FastAPI(title="Sovereign IRC Bridge", version="0.1.0")
app.include_router(health_router)

# TeaVM client = existing debug-oracle (no duplicate teavm-client build)
import os

_REPO_ROOT = Path(__file__).resolve().parents[2]
_env_static = os.environ.get("BRIDGE_STATIC_DEBUG_ORACLE", "").strip()
_DEBUG_ORACLE = Path(_env_static) if _env_static else (
    _REPO_ROOT
    / "games"
    / "teavm-rhythm"
    / "src"
    / "main"
    / "webapp"
    / "debug-oracle"
)
if _DEBUG_ORACLE.is_dir():
    app.mount(
        "/debug-oracle",
        StaticFiles(directory=str(_DEBUG_ORACLE), html=True),
        name="debug-oracle",
    )


@app.websocket("/ws")
async def websocket_bridge(websocket: WebSocket) -> None:
    await websocket.accept()
    settings = get_settings()
    proxy = WsTcpProxyStub(settings)
    try:
        await proxy.handle_websocket(websocket)
    except RuntimeError as exc:
        logger.warning("bridge refuse: %s", exc)
        try:
            await websocket.send_text(f"ERROR: {exc}")
            await websocket.close(code=1013)
        except WebSocketDisconnect:
            pass
    except WebSocketDisconnect:
        return


@app.get("/")
async def root() -> dict:
    return {
        "service": "sovereign-irc-bridge",
        "health": "/health",
        "ws": "/ws",
        "teavm_client": "/debug-oracle/",
        "irc": "irc.abjects.net (mTLS required for live dial; stub refuses without certs)",
    }


def run() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "src.main:app",
        host=s.bridge.ws_bind_host,
        port=s.bridge.ws_bind_port,
        log_level=s.deploy.log_level.lower(),
    )


if __name__ == "__main__":
    run()
