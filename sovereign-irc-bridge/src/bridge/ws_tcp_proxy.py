"""WebSocket-to-TCP byte forwarding — stub, fail-fast without certs."""
from __future__ import annotations

from ..models.settings import SovereignConfig
from .irc_client import IRCClientStub


class WsTcpProxyStub:
    def __init__(self, config: SovereignConfig) -> None:
        self._config = config
        self._irc = IRCClientStub(config.irc)

    async def handle_websocket(self, websocket) -> None:  # noqa: ANN001
        """Accept WS then fail-fast before any IRC TCP dial without mTLS."""
        # Ensure certs exist before touching the wire.
        self._config.irc.require_mtls()
        await websocket.close(code=1013, reason="bridge stub — no live IRC dial")
        raise RuntimeError(
            "WsTcpProxyStub: refuse live forward without a non-stub implementation"
        )
