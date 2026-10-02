#!/usr/bin/env python3
"""
scripts/cdp_status.py — /cdp/status handler for the Port 380 MCP server.

Honest state, no fabrication:
  - No attached CDP session   -> session_id and handover_latency_ms are null.
  - A reachable DevTools port -> reported as reachable, NOT as a session.
  - Reads do not append; only state transitions (attach / detach) write to
    symplectic_status.agent.jsonl by default.
  - record=1 may append a read line; write failures are returned, not swallowed.

Wire into port380_mcp.py:

    from scripts.cdp_status import register_cdp_status
    register_cdp_status(app)

Standalone:

    python3 scripts/cdp_status.py --once
    python3 scripts/cdp_status.py --once --probe
    python3 scripts/cdp_status.py --serve
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BIND_HOST = "127.0.0.1"  # never 0.0.0.0
STANDALONE_PORT = 3801
ROOT = Path(__file__).resolve().parent.parent
STATUS_STREAM = ROOT / "symplectic_status.agent.jsonl"
CDP_ENDPOINT = os.environ.get("CDP_ENDPOINT")


def _percentile(xs: list[float], p: int) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _carry_forward_core_fields() -> dict[str, Any]:
    empty = {"coherence": None, "phi_phase": None}
    try:
        if not STATUS_STREAM.exists():
            return empty
        with STATUS_STREAM.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 65536), os.SEEK_SET)
            tail = f.read().decode("utf-8", errors="replace")
        for line in reversed([ln for ln in tail.splitlines() if ln.strip()]):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "coherence" in obj:
                return {
                    "coherence": obj.get("coherence"),
                    "phi_phase": obj.get("phi_phase"),
                }
    except OSError:
        pass
    return empty


def _append_line(payload: dict[str, Any]) -> dict[str, Any]:
    """Append one JSONL line. Returns {ok: bool, error?: str}."""
    line = json.dumps(payload, sort_keys=True) + "\n"
    try:
        STATUS_STREAM.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            str(STATUS_STREAM), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644
        )
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
        return {"ok": True}
    except OSError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


class _SessionRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._session_id: Optional[str] = None
        self._ws_ready = False
        self._attached_at: Optional[float] = None
        self._latencies_ms: list[float] = []

    def attach(self, session_id: str) -> None:
        with self._lock:
            self._session_id = session_id
            self._ws_ready = True
            self._attached_at = time.time()
            self._latencies_ms = []

    def detach(self) -> None:
        with self._lock:
            self._session_id = None
            self._ws_ready = False
            self._attached_at = None

    def record_handover(self, latency_ms: float) -> None:
        with self._lock:
            if self._session_id is None:
                return
            self._latencies_ms.append(float(latency_ms))
            if len(self._latencies_ms) > 64:
                self._latencies_ms = self._latencies_ms[-64:]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            lat = list(self._latencies_ms)
            return {
                "session_id": self._session_id,
                "ws_ready": self._ws_ready,
                "attached_at": (
                    datetime.fromtimestamp(
                        self._attached_at, tz=timezone.utc
                    ).isoformat()
                    if self._attached_at
                    else None
                ),
                "sample_count": len(lat),
                "handover_latency_ms": lat[-1] if lat else None,
                "handover_p50_ms": _percentile(lat, 50) if lat else None,
                "handover_p95_ms": _percentile(lat, 95) if lat else None,
            }


_registry = _SessionRegistry()


def attach_session(session_id: str) -> dict[str, Any]:
    _registry.attach(session_id)
    core = _carry_forward_core_fields()
    write = _append_line(
        {
            "role": "cdp_bridge",
            "event": "cdp_status",
            "timestamp": _utcnow_iso(),
            "status": "attached",
            "session_id": session_id,
            "ws_ready": True,
            "coherence": core["coherence"],
            "phi_phase": core["phi_phase"],
        }
    )
    return {"attached": True, "write": write}


def detach_session() -> dict[str, Any]:
    snap = _registry.snapshot()
    _registry.detach()
    core = _carry_forward_core_fields()
    write = _append_line(
        {
            "role": "cdp_bridge",
            "event": "cdp_status",
            "timestamp": _utcnow_iso(),
            "status": "detached",
            "session_id": snap["session_id"],
            "ws_ready": False,
            "coherence": core["coherence"],
            "phi_phase": core["phi_phase"],
        }
    )
    return {"detached": True, "write": write}


def record_handover(latency_ms: float) -> None:
    _registry.record_handover(latency_ms)


def probe_endpoint(
    endpoint: Optional[str] = None, timeout_s: float = 0.5
) -> dict[str, Any]:
    target = endpoint or CDP_ENDPOINT
    if not target:
        return {
            "endpoint": None,
            "reachable": False,
            "reason": "CDP_ENDPOINT not set",
        }
    import urllib.error
    import urllib.request

    url = target.rstrip("/") + "/json/version"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read(2048)
            return {
                "endpoint": target,
                "reachable": True,
                "http_status": getattr(resp, "status", 200),
                "bytes": len(body),
            }
    except urllib.error.URLError as e:
        return {
            "endpoint": target,
            "reachable": False,
            "reason": f"URLError: {e.reason}",
        }
    except TimeoutError as e:
        return {
            "endpoint": target,
            "reachable": False,
            "reason": f"TimeoutError: {e}",
        }
    except OSError as e:
        return {
            "endpoint": target,
            "reachable": False,
            "reason": f"{type(e).__name__}: {e}",
        }


def cdp_status(probe: bool = False, record: bool = False) -> dict[str, Any]:
    snap = _registry.snapshot()
    payload: dict[str, Any] = {
        "event": "cdp_status",
        "timestamp": _utcnow_iso(),
        "status": "ok" if snap["ws_ready"] else "no_session",
        **snap,
    }
    if probe:
        payload["probe"] = probe_endpoint()
    if record:
        core = _carry_forward_core_fields()
        write = _append_line(
            {
                "role": "cdp_bridge",
                "event": "cdp_status",
                "timestamp": payload["timestamp"],
                "coherence": core["coherence"],
                "phi_phase": core["phi_phase"],
                "session_id": payload["session_id"],
                "ws_ready": payload["ws_ready"],
                "handover_latency_ms": payload["handover_latency_ms"],
                "status": payload["status"],
            }
        )
        payload["write"] = write
    return payload


def register_cdp_status(app) -> None:
    @app.get("/cdp/status")
    def _cdp_status(probe: int = 0, record: int = 0):
        return cdp_status(probe=bool(probe), record=bool(record))


def make_cdp_status_tool():
    def cdp_status_tool(probe: bool = False, record: bool = False) -> dict:
        return cdp_status(probe=probe, record=record)

    cdp_status_tool.__name__ = "cdp_status"
    cdp_status_tool.__doc__ = (
        "Return current CDP session state. Nulls when no session is attached."
    )
    return cdp_status_tool


def _serve_standalone(port: int) -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            u = urlparse(self.path)
            if u.path != "/cdp/status":
                self.send_response(404)
                self.end_headers()
                return
            q = parse_qs(u.query)
            probe = q.get("probe", ["0"])[0] not in ("0", "", "false")
            record = q.get("record", ["0"])[0] not in ("0", "", "false")
            body = json.dumps(
                cdp_status(probe=probe, record=record), indent=2
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    srv = ThreadingHTTPServer((BIND_HOST, port), Handler)
    print(f"cdp_status listening on http://{BIND_HOST}:{port}/cdp/status")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="cdp_status.py")
    ap.add_argument(
        "--serve",
        action="store_true",
        help=f"run standalone on {BIND_HOST}:{STANDALONE_PORT}",
    )
    ap.add_argument(
        "--once", action="store_true", help="print one JSON object and exit"
    )
    ap.add_argument(
        "--probe",
        action="store_true",
        help="include reachability probe (needs CDP_ENDPOINT)",
    )
    ap.add_argument("--port", type=int, default=STANDALONE_PORT)
    args = ap.parse_args(argv)

    if args.once:
        print(json.dumps(cdp_status(probe=args.probe), indent=2))
        return 0
    if args.serve:
        _serve_standalone(args.port)
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
