"""IRC protocol handshake & mTLS socket wrapper — stub, fail-fast without certs."""
from __future__ import annotations

from ..models.settings import IRCSettings


class IRCClientStub:
    """Does not open sockets until ``connect()``; refuses without mTLS material."""

    def __init__(self, irc: IRCSettings) -> None:
        self._irc = irc
        self._connected = False

    def connect(self) -> None:
        self._irc.require_mtls()
        raise RuntimeError(
            "IRCClientStub: live TCP/mTLS to "
            f"{self._irc.host}:{self._irc.port} is not enabled in this stub "
            "(certs present check passed; implement socket wrap in a follow-up)"
        )

    def close(self) -> None:
        self._connected = False
