#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ PULSE SERVICE — ENTRY 8930

Unified FRB + triune triangulation + NDJSON stream.

Modes:
  status       — bridge + triangulation snapshot
  pulse        — one FRB handshake pulse + post-pulse triangulation
  triangulate  — void estimate from triune anchors
  stream       — NDJSON real-time updates (asyncio generator)

Integration with:
  - FRB Bridge (quantum/frb_bridge.py)
  - Triune Triangulation (quantum/triune_triangulation.py)
  - Port 380 Implicit (quantum/port_380_implicit.py)
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)

Seal: ∀∞φ² · PULSE_SERVICE_8930 · WOOD_DRAGON_0.91 · SEALED
Witness: 8929 → 8930 — UNBROKEN
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional, List, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8930
SEAL = "∀∞φ² · PULSE_SERVICE_8930 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8929 → 8930 — UNBROKEN"

# ─── FRB Bridge ──────────────────────────────────────────────────────
try:
    from quantum.frb_bridge import FRB_BRIDGE, SEAL as FRB_SEAL
    FRB_AVAILABLE = True
except ImportError:
    FRB_BRIDGE = None
    FRB_SEAL = ""
    FRB_AVAILABLE = False

# ─── Triune Triangulation ────────────────────────────────────────────
try:
    from quantum.triune_triangulation import (
        handshake_triangulate,
        triune_delta,
        SEAL as TRIUNE_SEAL,
    )
    TRIUNE_AVAILABLE = True
except ImportError:
    handshake_triangulate = None
    triune_delta = None
    TRIUNE_SEAL = ""
    TRIUNE_AVAILABLE = False

# ─── Port 380 Implicit ──────────────────────────────────────────────
try:
    from quantum.port_380_implicit import PARAMETER_TABLE
    IMPLICIT_AVAILABLE = True
except ImportError:
    PARAMETER_TABLE = {}
    IMPLICIT_AVAILABLE = False

# ─── Security ────────────────────────────────────────────────────────
try:
    from quantum.security import status as security_status
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False


# ─── Helpers ──────────────────────────────────────────────────────────

def _now() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _param_summary() -> Dict[str, Any]:
    """JSON-safe slice of PARAMETER_TABLE (skip huge floats noise)."""
    if not PARAMETER_TABLE:
        return {}

    keys = (
        "entry_8706",
        "entry_8927",
        "entry_8928",
        "wood_dragon",
        "triune_delta",
        "dual_delta_eridanus",
        "temporal_anchors",
        "triune_temporal_anchors",
        "seal_8706",
        "seal_8927",
        "seal_8928",
        "triune_seal",
        "dual_delta_seal",
        "phase_lock_deg",
    )

    out: Dict[str, Any] = {}
    for k in keys:
        if k in PARAMETER_TABLE:
            out[k] = PARAMETER_TABLE[k]
    return out


# ─── Pulse Service ──────────────────────────────────────────────────

class PulseService:
    """
    Unified pulse surface over FRB bridge + triune triangulation.

    Provides:
      - status: snapshot of FRB bridge and triangulation
      - pulse: one FRB handshake pulse + post-pulse triangulation
      - triangulate: void estimate from triune anchors
      - stream: NDJSON real-time updates
    """

    def __init__(self) -> None:
        self.frb = FRB_BRIDGE
        self._streaming = False
        self._pulse_count = 0
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100

    def status(self) -> Dict[str, Any]:
        """Get the current status snapshot."""
        # FRB status
        if self.frb is not None and FRB_AVAILABLE:
            frb_status = self.frb.status()
        else:
            frb_status = {"error": "FRB bridge unavailable"}

        # Triune triangulation
        if handshake_triangulate is not None and TRIUNE_AVAILABLE:
            tri = handshake_triangulate()
        else:
            tri = {"error": "Triune triangulation unavailable"}

        # Triune delta
        if triune_delta is not None and TRIUNE_AVAILABLE:
            delta = triune_delta()
        else:
            delta = {}

        return {
            "timestamp": _now(),
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
            "frb": frb_status,
            "triangulation": tri,
            "triune_delta": delta,
            "parameter_table": _param_summary(),
            "frb_seal": FRB_SEAL,
            "triune_seal": TRIUNE_SEAL,
            "services": {
                "frb": FRB_AVAILABLE,
                "triune": TRIUNE_AVAILABLE,
                "implicit": IMPLICIT_AVAILABLE,
                "security": SECURITY_AVAILABLE,
            },
            "pulse_count": self._pulse_count,
            "history_count": len(self._history),
        }

    def pulse(self) -> Dict[str, Any]:
        """
        Execute one FRB handshake pulse and post-pulse triangulation.

        Returns:
            Dictionary with pulse results and post-pulse triangulation.
        """
        self._pulse_count += 1

        # Execute FRB pulse
        if self.frb is not None and FRB_AVAILABLE:
            pulse_result = self.frb.pulse_once()
        else:
            pulse_result = {"error": "FRB bridge unavailable"}

        # Post-pulse triangulation
        if handshake_triangulate is not None and TRIUNE_AVAILABLE:
            tri = handshake_triangulate()
        else:
            tri = {"error": "Triune triangulation unavailable"}

        result = {
            "pulse_id": self._pulse_count,
            "pulse": pulse_result,
            "triangulation_after": tri,
            "timestamp": _now(),
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
        }

        # Store history
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return result

    def triangulate(self) -> Dict[str, Any]:
        """
        Perform void estimate from triune anchors.

        Returns:
            Dictionary with triangulation results.
        """
        if handshake_triangulate is None or not TRIUNE_AVAILABLE:
            return {
                "error": "Triune triangulation unavailable",
                "entry": ENTRY,
                "seal": SEAL,
                "timestamp": _now(),
            }

        body = handshake_triangulate()
        body["timestamp"] = _now()
        body["entry"] = ENTRY
        body["seal"] = SEAL
        body["witness"] = WITNESS
        return body

    async def stream_updates(
        self,
        interval: float = 1.0,
        max_events: int = 0,
    ) -> AsyncGenerator[str, None]:
        """
        Yield NDJSON real-time updates.

        Args:
            interval: Time between updates in seconds.
            max_events: Maximum number of events (0 = unbounded).

        Yields:
            NDJSON strings with status updates.
        """
        yield json.dumps({
            "event": "start",
            "mode": "stream",
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": _now(),
        }) + "\n"

        count = 0
        while True:
            st = self.status()
            frb = st.get("frb") or {}
            tri = st.get("triangulation") or {}

            # Extract void estimate
            void = None
            if isinstance(tri, dict):
                void = tri.get("void")

            line = {
                "event": "delta",
                "count": count,
                "pulse_count": st.get("pulse_count", 0),
                "frb_pulse_count": frb.get("pulse_count"),
                "frb_coherence": frb.get("coherence"),
                "frb_harmony_index": frb.get("harmony_index"),
                "void_estimate": void,
                "triangulation_error": tri.get("error") if isinstance(tri, dict) else None,
                "timestamp": _now(),
                "entry": ENTRY,
                "seal": SEAL,
            }

            yield json.dumps(line, default=str) + "\n"

            count += 1
            if max_events and count >= max_events:
                yield json.dumps({
                    "event": "complete",
                    "count": count,
                    "entry": ENTRY,
                    "seal": SEAL,
                    "timestamp": _now(),
                }) + "\n"
                return

            await asyncio.sleep(interval)

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get pulse history."""
        if limit is not None:
            return self._history[-limit:]
        return self._history

    def reset(self) -> None:
        """Reset the service state."""
        self._pulse_count = 0
        self._history = []


# ─── Singleton ──────────────────────────────────────────────────────

PULSE = PulseService()


# ─── Request Handler ─────────────────────────────────────────────────

def handle_request(mode: str = "status", **kwargs: Any) -> Any:
    """
    Handle a request to the pulse service.

    Args:
        mode: Request mode ('status', 'pulse', 'triangulate', 'stream').
        **kwargs: Additional arguments.

    Returns:
        Response data or AsyncGenerator for stream mode.
    """
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

    if mode == "history":
        limit = kwargs.get("limit")
        return PULSE.get_history(limit)

    return {
        "error": "Unknown mode",
        "available": ["status", "pulse", "triangulate", "stream", "history"],
        "entry": ENTRY,
        "seal": SEAL,
        "timestamp": _now(),
    }


# ─── Security Integration ────────────────────────────────────────────

def pulse_security_status() -> Dict[str, Any]:
    """Get security status for the pulse service."""
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def pulse_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the pulse service."""
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified pulse service — Entry 8930",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--mode",
        default="status",
        choices=["status", "pulse", "triangulate", "stream", "history"],
        help="Service mode",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Stream interval in seconds",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=3,
        help="Stream: stop after N deltas (0=forever)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="History: number of entries to show",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ PULSE SERVICE — Integration Status")
        print("=" * 40)
        print(f"  FRB Bridge: {'✅' if FRB_AVAILABLE else '❌'}")
        print(f"  Triune: {'✅' if TRIUNE_AVAILABLE else '❌'}")
        print(f"  Implicit: {'✅' if IMPLICIT_AVAILABLE else '❌'}")
        print(f"  Security: {'✅' if SECURITY_AVAILABLE else '❌'}")
        return 0

    if args.mode == "stream":

        async def _run() -> None:
            async for line in PULSE.stream_updates(args.interval, args.max_events):
                print(line, end="", flush=True)

        asyncio.run(_run())
        return 0

    if args.mode == "history":
        history = PULSE.get_history(limit=args.limit)
        if args.json:
            print(json.dumps(history, indent=2, default=str))
        else:
            print("🜁∀ PULSE SERVICE — History")
            print("=" * 55)
            print(f"  Entries: {len(history)}")
            for entry in history:
                pulse_id = entry.get("pulse_id", "?")
                ts = entry.get("timestamp", "?")
                print(f"    Pulse {pulse_id}: {ts}")
        return 0

    result = handle_request(args.mode)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if args.mode == "status":
            print("🜁∀ PULSE SERVICE — Status")
            print("=" * 55)
            print(f"  Entry: {ENTRY}")
            print(f"  Seal: {SEAL}")
            print(f"  Witness: {WITNESS}")
            print(f"  FRB: {'✅' if result.get('services', {}).get('frb', False) else '❌'}")
            print(f"  Triune: {'✅' if result.get('services', {}).get('triune', False) else '❌'}")
            print(f"  Pulse count: {result.get('pulse_count', 0)}")
            frb = result.get('frb', {})
            print(f"  FRB coherence: {frb.get('coherence', 'N/A')}")
            tri = result.get('triangulation', {})
            print(f"  Void estimate: {tri.get('void', 'N/A')}")
        else:
            print(json.dumps(result, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
