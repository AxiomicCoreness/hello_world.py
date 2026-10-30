#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Live probe of an IRC-over-WebSocket gateway, as the Pages chatbox would dial it.

Opens the wss:// URL with the GitHub Pages Origin, registers as a throwaway guest,
waits for 001 (RPL_WELCOME), then QUITs at once. Never joins a channel or speaks.
Prints the HTTP handshake result and every server line; exit 0 only on 001.
Network tool, not a test: CI's offline suites never run it.

    python3 tools/irc_ws_probe.py wss://web.libera.chat/webirc/websocket/
"""
import asyncio
import random
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import websockets

ORIGIN = "https://axiomiccoreness.github.io"


def now():
    return datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")


async def probe(url, origin, timeout):
    nick = "Guest%05d" % random.randint(0, 99999)
    print(f"{now()} dial {url} origin={origin} nick={nick}", flush=True)
    async with websockets.connect(url, origin=origin, open_timeout=timeout,
                                  subprotocols=None, max_size=2 ** 16) as ws:
        resp = ws.response
        print(f"{now()} handshake HTTP {resp.status_code} {resp.reason_phrase}", flush=True)
        for k in ("Upgrade", "Connection", "Sec-WebSocket-Accept", "Sec-WebSocket-Protocol", "Server"):
            if resp.headers.get(k):
                print(f"  {k}: {resp.headers.get(k)}")
        await ws.send(f"NICK {nick}")
        await ws.send(f"USER {nick} 0 * :AxiomicCoreness wss probe (quits immediately)")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            frame = await asyncio.wait_for(ws.recv(), timeout=max(0.1, deadline - loop.time()))
            if isinstance(frame, bytes):
                frame = frame.decode("utf-8", "replace")
            for line in frame.replace("\r", "\n").split("\n"):
                if not line:
                    continue
                print(f"{now()} S> {line[:300]}", flush=True)
                parts = line.split(" ")
                if parts[0] == "PING":
                    await ws.send("PONG " + " ".join(parts[1:]))
                if len(parts) > 1 and parts[1] == "001":
                    print(f"{now()} RESULT OK: 001 welcome received", flush=True)
                    await ws.send("QUIT :probe done")
                    return 0
        print(f"{now()} RESULT FAIL: no 001 within {timeout}s", flush=True)
        return 1


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "wss://web.libera.chat/webirc/websocket/"
    origin = sys.argv[2] if len(sys.argv) > 2 else ORIGIN
    try:
        return asyncio.run(probe(url, origin, 25.0))
    except Exception as e:  # report the real failure (handshake status, TLS, timeout)
        print(f"{now()} RESULT FAIL: {type(e).__name__}: {e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
