#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌀∀ Pulse Service — unified FRB + triune triangulation + NDJSON stream.

Modes:
  status       — bridge + triangulation snapshot
  pulse        — one FRB handshake pulse + post-pulse triangulation
  triangulate  — void estimate from triune anchors
  stream       — NDJSON real-time updates (asyncio generator)

Seal: ∀∞φ² · PULSE_SERVICE_8930 · WOOD_DRAGON_0.91 · SEALED
Witness: 8929 → 8930 — UNBROKEN
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

SEAL_CORE = "∀∞φ² · PULSE_SERVICE_8930 · WOOD_DRAGON_0.91 · SEALED"

try:
    from quantum.frb_bridge import FRB_BRIDGE, SEAL_CORE as FRB_SEAL
except Exception:  # pragma: no cover
    FRB_BRIDGE = None  # type: ignore
    FRB_SEAL = ""

try:
    from quantum.triune_triangulation import (
        handshake_triangulate,
        triune_delta,
        SEAL_CORE as TRIUNE_SEAL,
    )
except Exception:  # pragma: no cover
    handshake_triangulate = None  # type: ignore
    triune_delta = None  # type: ignore
    TRIUNE_SEAL = ""

try:
    from quantum.port_380_implicit import PARAMETER_TABLE
except Exception:  # pragma: no cover
    PARAMETER_TABLE = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _param_summary() -> Dict[str, Any]:
    """JSON-safe slice of PARAMETER_TABLE (skip huge floats noise)."""
    if not PARAMETER_TABLE:
        return {}
    keys = (
        "wood_dragon",
        "triune_delta",
        "dual_delta_eridanus",
        "temporal_anchors",
        "triune_temporal_anchors",
        "seal",
        "triune_seal",
        "dual_delta_seal",
    )
    out: Dict[str, Any] = {}
    for k in keys:
        if k in PARAMETER_TABLE:
            out[k] = PARAMETER_TABLE[k]
    return out


class PulseService:
    """Unified pulse surface over FRB bridge + triune triangulation."""

    def __init__(self) -> None:
        self.frb = FRB_BRIDGE
        self._streaming = False

    def status(self) -> Dict[str, Any]:
        frb_status = self.frb.status() if self.frb is not None else {"error": "frb unavailable"}
        tri = handshake_triangulate() if handshake_triangulate else {"error": "triune unavailable"}
        return {
            "timestamp": _now(),
            "frb": frb_status,
            "triangulation": tri,
            "triune_delta": triune_delta() if triune_delta else {},
            "parameter_table": _param_summary(),
            "seal": SEAL_CORE,
            "frb_seal": FRB_SEAL,
            "triune_seal": TRIUNE_SEAL,
        }

    def pulse(self) -> Dict[str, Any]:
        if self.frb is None:
            return {"error": "frb unavailable", "seal": SEAL_CORE}
        result = self.frb.pulse_once()
        tri = handshake_triangulate() if handshake_triangulate else {}
        return {
            "pulse": result,
            "triangulation_after": tri,
            "timestamp": _now(),
            "seal": SEAL_CORE,
        }

    def triangulate(self) -> Dict[str, Any]:
        if not handshake_triangulate:
            return {"error": "triune unavailable", "seal": SEAL_CORE}
        body = handshake_triangulate()
        body["timestamp"] = _now()
        body["pulse_seal"] = SEAL_CORE
        return body

    async def stream_updates(self, interval: float = 1.0, max_events: int = 0) -> AsyncGenerator[str, None]:
        """Yield NDJSON lines. max_events=0 means unbounded (until cancelled)."""
        yield json.dumps({"event": "start", "mode": "stream", "seal": SEAL_CORE}) + "\n"
        count = 0
        while True:
            st = self.status()
            frb = st.get("frb") or {}
            tri = st.get("triangulation") or {}
            void = tri.get("void") if isinstance(tri, dict) else None
            line = {
                "event": "delta",
                "count": count,
                "frb_pulse_count": frb.get("pulse_count"),
                "harmony_index": frb.get("harmony_index"),
                "coherence": frb.get("coherence"),
                "void_estimate": void,
                "triangulation_error": tri.get("error") if isinstance(tri, dict) else None,
                "timestamp": _now(),
                "seal": SEAL_CORE,
            }
            yield json.dumps(line, default=str) + "\n"
            count += 1
            if max_events and count >= max_events:
                yield json.dumps(
                    {"event": "complete", "count": count, "seal": SEAL_CORE}
                ) + "\n"
                return
            await asyncio.sleep(interval)


PULSE = PulseService()


def handle_request(mode: str = "status", **kwargs: Any) -> Any:
    mode = (mode or "status").lower()
    if mode == "status":
        return PULSE.status()
    if mode == "pulse":
        return PULSE.pulse()
    if mode == "triangulate":
        return PULSE.triangulate()
    if mode == "stream":
        return PULSE.stream_updates(
            interval=float(kwargs.get("interval", 1.0)),
            max_events=int(kwargs.get("max_events", 0)),
        )
    return {
        "error": "Unknown mode",
        "available": ["status", "pulse", "triangulate", "stream"],
        "seal": SEAL_CORE,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Unified pulse service")
    parser.add_argument(
        "--mode",
        default="status",
        choices=["status", "pulse", "triangulate", "stream"],
    )
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument(
        "--max-events",
        type=int,
        default=3,
        help="stream only: stop after N deltas (0=forever)",
    )
    args = parser.parse_args()

    if args.mode == "stream":

        async def _run() -> None:
            async for line in PULSE.stream_updates(args.interval, args.max_events):
                print(line, end="", flush=True)

        asyncio.run(_run())
    else:
        print(json.dumps(handle_request(args.mode), indent=2, default=str))


if __name__ == "__main__":
    main()
