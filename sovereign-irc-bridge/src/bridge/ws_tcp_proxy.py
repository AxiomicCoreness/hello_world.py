"""WebSocket-to-TCP byte pump (mTLS IRC).

Actively forwards raw WebSocket bytes ↔ TCP after ``IRCClient.connect()``.
Config load already ValidationError-fails without mTLS PEMs.
"""
from __future__ import annotations

import asyncio
import logging

from ..models.settings import SovereignConfig
from .irc_client import IRCClient

logger = logging.getLogger("sovereign-irc-bridge.pump")


class WsTcpProxy:
    def __init__(self, config: SovereignConfig) -> None:
        self._config = config
        self._irc = IRCClient(config.irc)

    async def handle_websocket(self, websocket) -> None:  # noqa: ANN001
        max_buf = self._config.bridge.max_buffer_size
        reader, writer = await self._irc.connect()
        logger.info(
            "pump up %s:%s max_buffer=%s",
            self._config.irc.host,
            self._config.irc.port,
            max_buf,
        )

        async def ws_to_tcp() -> None:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                data = message.get("bytes")
                if data is None and message.get("text") is not None:
                    data = message["text"].encode("utf-8")
                if not data:
                    continue
                writer.write(data[:max_buf])
                await writer.drain()

        async def tcp_to_ws() -> None:
            while True:
                chunk = await reader.read(max_buf)
                if not chunk:
                    break
                await websocket.send_bytes(chunk)

        try:
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(ws_to_tcp(), name="ws→tcp"),
                    asyncio.create_task(tcp_to_ws(), name="tcp→ws"),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()
            for t in done:
                exc = t.exception()
                if exc is not None:
                    raise exc
        finally:
            await self._irc.close()
            try:
                await websocket.close()
            except Exception:
                pass


# Back-compat alias
WsTcpProxyStub = WsTcpProxy
