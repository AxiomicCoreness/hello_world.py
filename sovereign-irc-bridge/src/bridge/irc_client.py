"""IRC mTLS TCP client — opens SSL socket only after cert validation."""
from __future__ import annotations

import asyncio
import ssl
from typing import Optional, Tuple

from ..models.settings import IRCSettings


class IRCClient:
    """mTLS TCP client to irc.abjects.net (or configured host)."""

    def __init__(self, irc: IRCSettings) -> None:
        self._irc = irc
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        cert, key, ca = self._irc.require_mtls()
        ctx = ssl.create_default_context(cafile=str(ca))
        ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
        reader, writer = await asyncio.open_connection(
            self._irc.host,
            self._irc.port,
            ssl=ctx,
            server_hostname=self._irc.host,
        )
        self._reader, self._writer = reader, writer
        return reader, writer

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None


# Back-compat alias for older imports
IRCClientStub = IRCClient
