"""FastAPI entry: health + WebSocket byte pump; TeaVM debug-oracle static assets."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .api.health import router as health_router
from .bridge.ws_tcp_proxy import WsTcpProxy
from .models.settings import get_settings

logger = logging.getLogger("sovereign-irc-bridge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail-fast: ValidationError if IRC__MTLS_* missing / PEM absent — before serving.
    settings = get_settings()
    logger.info(
        "mTLS ok host=%s:%s cert=%s",
        settings.irc.host,
        settings.irc.port,
        settings.irc.mtls_cert_path,
    )
    yield


app = FastAPI(title="Sovereign IRC Bridge", version="0.1.1", lifespan=lifespan)
app.include_router(health_router)

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
    proxy = WsTcpProxy(settings)
    try:
        await proxy.handle_websocket(websocket)
    except Exception as exc:
        logger.warning("bridge pump error: %s", exc)
        try:
            await websocket.send_text(f"ERROR: {exc}")
            await websocket.close(code=1013)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass


@app.get("/")
async def root() -> dict:
    return {
        "service": "sovereign-irc-bridge",
        "health": "/health",
        "ws": "/ws",
        "teavm_client": "/debug-oracle/",
        "irc": "irc.abjects.net",
        "live_wire": "WS↔TCP mTLS byte pump (requires IRC__MTLS_* PEMs at startup)",
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
