"""TeaVM CLI WebSocket — Cosmic Alignment loopback bind.

Binds **127.0.0.1:6669** only (never 0.0.0.0). Path {@code /cli}.

Browser contract: {@code ws://127.0.0.1:6669/cli}
Remote label behind this bridge: {@code irc.abjects.net:6669}

Default mode is local echo / Engine stubs (no outbound IRC) so CI stays
offline. Set {@code CLI_LIVE_IRC=1} to open a plain TCP dial to the remote
label (still from this process, not from the browser).

pythonIDE path: lines starting with ``/py``, ``py``, ``/ide``, or ``ide``
are routed through ``pythonIDE.toolkit.SovereignToolkit`` (and pointer_2300
for ``pointer``). Failures are sent back as ``[Traceback]`` lines so the
TeaVM chat history shows a useful Python traceback.
"""
from __future__ import annotations

import ast
import asyncio
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Final, List, Optional

logger = logging.getLogger("sovereign-irc-bridge.cli")

LOOPBACK_HOST: Final = "127.0.0.1"
CLI_PORT: Final = 6669
REMOTE_IRC: Final = "irc.abjects.net:6669"
ALLOWED_BIND: Final = frozenset({"127.0.0.1", "::1"})

# Repo root (…/hello_world.py) so `pythonIDE` imports resolve when the bridge
# is started from sovereign-irc-bridge/.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def assert_loopback_bind(host: str) -> str:
    """Non-negotiable: CLI must not listen on 0.0.0.0 / LAN interfaces."""
    h = (host or "").strip()
    if h not in ALLOWED_BIND:
        raise RuntimeError(
            f"CLI Cosmic Alignment requires bind in {sorted(ALLOWED_BIND)}, got {host!r}"
        )
    return h


def _is_ide_line(text: str) -> bool:
    t = (text or "").strip().lower()
    return (
        t.startswith("/py")
        or t.startswith("/ide")
        or t.startswith("py ")
        or t == "py"
        or t.startswith("ide ")
        or t == "ide"
        or t.startswith("/pythonide")
        or t == "/pythonide"
    )


def _strip_verb(text: str) -> str:
    t = (text or "").strip()
    lower = t.lower()
    for v in ("/pythonide", "/py", "/ide", "pythonide", "py", "ide"):
        if lower == v:
            return ""
        if lower.startswith(v + " "):
            return t[len(v) :].strip()
    return t


def _traceback_lines(exc: Optional[BaseException] = None) -> List[str]:
    if exc is not None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    else:
        tb = traceback.format_exc()
    out: List[str] = []
    for line in tb.rstrip().splitlines():
        out.append(f"[Traceback] {line}")
    return out


def _parse_call_args(raw: str) -> tuple:
    """Parse trailing args with ast.literal_eval for safety (no exec)."""
    raw = (raw or "").strip()
    if not raw:
        return ()
    try:
        val = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        parts = raw.split()
        out: list = []
        for p in parts:
            try:
                out.append(ast.literal_eval(p))
            except (SyntaxError, ValueError):
                out.append(p)
        return tuple(out)
    if isinstance(val, tuple):
        return val
    return (val,)


def handle_pythonide(text: str) -> List[str]:
    """Run a pythonIDE CLI command; always returns chat-tagged lines."""
    lines: List[str] = []
    rest = _strip_verb(text)
    if not rest or rest.lower() in {"help", "?"}:
        lines.append("[System] pythonIDE CLI · toolkit.py + pointer_2300")
        lines.append("[Engine] commands: help | list | call <cap> [args] | pointer")
        lines.append(f"[Engine] dial {LOOPBACK_HOST}:{CLI_PORT}/cli · NO_LEDGER_WRITE")
        return lines

    parts = rest.split(None, 2)
    cmd = parts[0].lower()

    try:
        if cmd in {"list", "ls"}:
            from pythonIDE.toolkit import SovereignToolkit

            tk = SovereignToolkit()
            caps = tk.list()
            lines.append(f"[Engine] pythonIDE toolkit · {tk.count()} capabilities")
            lines.append("[Engine] " + ", ".join(caps))
            stubs = tk.stubs()
            if stubs:
                lines.append("[System] stubs: " + ", ".join(stubs))
            return lines

        if cmd in {"pointer", "2300"}:
            from pythonIDE.pointer_2300 import pointer_payload

            payload = pointer_payload()
            lines.append(
                f"[Engine] pointer {payload.get('pointer_id')} → "
                f"Context Layer {payload.get('context_layer')} · {payload.get('domain')}"
            )
            lines.append(
                "[Engine] author="
                + str(payload.get("author"))
                + " · anchor="
                + str(payload.get("anchors", {}).get("anchor", ""))
            )
            lines.append("[Engine] " + json.dumps(payload, sort_keys=True)[:1500])
            return lines

        if cmd in {"call", "run"}:
            if len(parts) < 2:
                raise TypeError("call requires capability name — /py call <name> [args]")
            name = parts[1]
            arg_raw = parts[2] if len(parts) > 2 else ""
            args = _parse_call_args(arg_raw)
            from pythonIDE.toolkit import SovereignToolkit

            tk = SovereignToolkit()
            result = tk.call(name, *args)
            rendered = result if isinstance(result, str) else json.dumps(result, default=str)
            lines.append(f"[Engine] {name} → {rendered}")
            return lines

        from pythonIDE.toolkit import SovereignToolkit

        tk = SovereignToolkit()
        if cmd in tk.list():
            result = tk.call(cmd)
            rendered = result if isinstance(result, str) else json.dumps(result, default=str)
            lines.append(f"[Engine] {cmd} → {rendered}")
            return lines

        raise ValueError(
            f"unknown ide command: {cmd} — try /py help | /py list | /py call <cap> | /py pointer"
        )
    except Exception as exc:  # noqa: BLE001 — surface full traceback to chat UI
        lines.append(f"[System] pythonIDE error: {type(exc).__name__}: {exc}")
        lines.extend(_traceback_lines(exc))
        return lines


def create_app():
    """Build the FastAPI app (import fastapi only when serving)."""
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    app = FastAPI(title="Sovereign IRC CLI loopback", version="0.2.0")

    @app.get("/health")
    async def health() -> dict:
        return {
            "service": "sovereign-irc-bridge-cli",
            "bind": f"{LOOPBACK_HOST}:{CLI_PORT}",
            "path": "/cli",
            "remote": REMOTE_IRC,
            "live_irc": os.environ.get("CLI_LIVE_IRC", "0") == "1",
            "pythonide": True,
        }

    @app.websocket("/cli")
    async def cli_socket(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_text(f"[System] loopback CLI on {LOOPBACK_HOST}:{CLI_PORT}/cli")
        await websocket.send_text(f"[Engine] path → {REMOTE_IRC} (browser never dials abjects)")
        await websocket.send_text(
            "[Engine] pythonIDE: /py help · /py list · /py call <cap> · /py pointer"
        )
        live = os.environ.get("CLI_LIVE_IRC", "0") == "1"
        reader = writer = None
        if live:
            host, _, port_s = REMOTE_IRC.partition(":")
            try:
                reader, writer = await asyncio.open_connection(host, int(port_s))
                await websocket.send_text(f"[Engine] live TCP open → {REMOTE_IRC}")
            except Exception as exc:  # noqa: BLE001 — surface to CLI UI
                await websocket.send_text(f"[System] live TCP failed: {exc} · staying stub")
                for line in _traceback_lines(exc):
                    await websocket.send_text(line)
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
                if _is_ide_line(text):
                    for line in handle_pythonide(text):
                        await websocket.send_text(line)
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
                                    "[Engine] "
                                    + chunk.decode("utf-8", errors="replace").rstrip()
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

    return app


# ASGI entry used by uvicorn / Dockerfile when fastapi is installed.
try:
    app = create_app()
except ModuleNotFoundError:
    app = None  # type: ignore[assignment]


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
