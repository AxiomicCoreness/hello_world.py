"""TeaVM CLI WebSocket — Cosmic Alignment loopback bind.

Binds **127.0.0.1:6669** only (never 0.0.0.0). Path {@code /cli}.

Browser contract: {@code ws://127.0.0.1:6669/cli}
Remote label behind this bridge: {@code irc.abjects.net:6669}

Default mode is local echo / Engine stubs (no outbound IRC) so CI stays
offline. Set {@code CLI_LIVE_IRC=1} to open a plain TCP dial to the remote
label (still from this process, not from the browser).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Final

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logger = logging.getLogger("sovereign-irc-bridge.cli")

LOOPBACK_HOST: Final = "127.0.0.1"
CLI_PORT: Final = 6669
REMOTE_IRC: Final = "irc.abjects.net:6669"
ALLOWED_BIND: Final = frozenset({"127.0.0.1", "::1"})


def assert_loopback_bind(host: str) -> str:
    """Non-negotiable: CLI must not listen on 0.0.0.0 / LAN interfaces."""
    h = (host or "").strip()
    if h not in ALLOWED_BIND:
        raise RuntimeError(
            f"CLI Cosmic Alignment requires bind in {sorted(ALLOWED_BIND)}, got {host!r}"
        )
    return h


app = FastAPI(title="Sovereign IRC CLI loopback", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {
        "service": "sovereign-irc-bridge-cli",
        "bind": f"{LOOPBACK_HOST}:{CLI_PORT}",
        "path": "/cli",
        "remote": REMOTE_IRC,
        "live_irc": os.environ.get("CLI_LIVE_IRC", "0") == "1",
    }


@app.websocket("/cli")
async def cli_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_text(f"[System] loopback CLI on {LOOPBACK_HOST}:{CLI_PORT}/cli")
    await websocket.send_text(f"[Engine] path → {REMOTE_IRC} (browser never dials abjects)")
    live = os.environ.get("CLI_LIVE_IRC", "0") == "1"
    reader = writer = None
    if live:
        host, _, port_s = REMOTE_IRC.partition(":")
        try:
            reader, writer = await asyncio.open_connection(host, int(port_s))
            await websocket.send_text(f"[Engine] live TCP open → {REMOTE_IRC}")
        except Exception as exc:  # noqa: BLE001 — surface to CLI UI
            await websocket.send_text(f"[System] live TCP failed: {exc} · staying stub")
            reader = writer = None
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            text = message.get("text")
            if text is None and message.get("bytes") is not None:
                text = message["bytes"].decode("utf-8", errors="replace")
            if not text:
                continue
            await websocket.send_text(f"[Engine] ack: {text}")
            if writer is not None:
                writer.write((text.rstrip("\r\n") + "\r\n").encode("utf-8"))
                await writer.drain()
                if reader is not None:
                    try:
                        chunk = await asyncio.wait_for(reader.read(4096), timeout=0.4)
                        if chunk:
                            await websocket.send_text(
                                "[Engine] " + chunk.decode("utf-8", errors="replace").rstrip()
                            )
                    except asyncio.TimeoutError:
                        pass
    except WebSocketDisconnect:
        pass
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


def run() -> None:
    import uvicorn

    host = assert_loopback_bind(os.environ.get("CLI_BIND_HOST", LOOPBACK_HOST))
    port = int(os.environ.get("CLI_BIND_PORT", str(CLI_PORT)))
    if port != CLI_PORT:
        logger.warning("non-default CLI port %s (contract is %s)", port, CLI_PORT)
    logger.info("CLI loopback bind %s:%s /cli → remote %s", host, port, REMOTE_IRC)
    uvicorn.run(
        "src.cli_loopback:app",
        host=host,
        port=port,
        log_level=os.environ.get("DEPLOY_LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run()
