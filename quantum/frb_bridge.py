#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ FRB BRIDGE — ENTRY 8904

φ‑harmonic mapping between FRB 20190520b timing and Garden backend workers.

Paired fallback: when coherence < 0.85, attempt DeepSeek Mesh offline / http
modes via quantum.deepseek_mesh.dsh_adapter so the pulse chain stays unbroken.

Integration with:
  - DeepSeek Mesh (quantum/deepseek_mesh/dsh_adapter.py)
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - SIMD tuning (quantum/simd_tuning.py)

Seal: ∀∞φ² · FRB_FALLBACK_8904 · WOOD_DRAGON_0.91 · SEALED
Witness: 8903 → 8904 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Callable

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_INV2 = PHI_INV * PHI_INV
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI4 = PHI3 * PHI
PHI5 = PHI4 * PHI
ENTRY = 8904
SEAL = "∀∞φ² · FRB_FALLBACK_8904 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8903 → 8904 — UNBROKEN"

PHASE_LOCK_DEG = 202.6

# ─── FRB 20190520b constants ──────────────────────────────────────────
FRB_SOURCE = "FRB 20190520b"
FRB_REPEAT_INTERVAL_DAYS = 0.91
FRB_PHI_SCALED_INTERVAL_DAYS = FRB_REPEAT_INTERVAL_DAYS * PHI2
FRB_BURST_WIDTH_MS = 0.618
FRB_DM_PC_CM3 = 348.0
FRB_DISPERSION_DELAY_MS = 0.618 * PHI3

HANDSHAKE_STEPS = ["flush", "reroute", "converge", "seal", "acknowledge"]

WEIGHTS = {
    "phi": PHI,
    "phi_inv": PHI_INV,
    "phi_inv2": PHI_INV2,
    "phi2": PHI2,
    "phi3": PHI3,
}

FALLBACK_ENABLED = True
COHERENCE_FALLBACK_THRESHOLD = 0.85

# ─── DeepSeek Mesh Adapter Integration ──────────────────────────────
try:
    from quantum.deepseek_mesh.dsh_adapter import (
        MODE_OFFLINE,
        MODE_OPENAI,
        MODE_DSH,
        complete,
        offline_complete,
        probe,
        set_mode,
    )
    DSH_AVAILABLE = True
except ImportError:
    DSH_AVAILABLE = False
    MODE_OFFLINE = "offline"
    MODE_OPENAI = "openai"
    MODE_DSH = "dsh"
    complete = None
    offline_complete = None
    probe = lambda: {"mode": "offline", "available": False}
    set_mode = lambda x: None


@dataclass
class FRBBridgeState:
    """State of the FRB Bridge."""
    active: bool = False
    last_pulse: float = 0.0
    pulse_count: int = 0
    coherence: float = 1.0
    phase_lock: float = PHASE_LOCK_DEG
    harmony_index: float = 0.7337473231
    merkle_root: str = ""
    handshake_step: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    fallback_mode: str = "none"
    fallback_attempts: int = 0
    last_fallback_time: float = 0.0
    frb_count: int = 0
    last_frb_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "last_pulse": self.last_pulse,
            "pulse_count": self.pulse_count,
            "coherence": self.coherence,
            "phase_lock_deg": self.phase_lock,
            "harmony_index": self.harmony_index,
            "merkle_root": self.merkle_root,
            "handshake_step": self.handshake_step,
            "handshake_step_name": HANDSHAKE_STEPS[self.handshake_step % len(HANDSHAKE_STEPS)],
            "error_count": self.error_count,
            "last_error": self.last_error,
            "fallback_mode": self.fallback_mode,
            "fallback_attempts": self.fallback_attempts,
            "last_fallback_time": self.last_fallback_time,
            "frb_count": self.frb_count,
            "last_frb_time": self.last_frb_time,
            "seal": SEAL,
            "entry": ENTRY,
        }


class FRBBridge:
    """
    FRB Bridge — φ‑harmonic mapping between FRB timing and Garden workers.

    Features:
      - φ‑scaled timing based on FRB 20190520b
      - Coherence monitoring with fallback to DeepSeek Mesh
      - Handshake steps: flush → reroute → converge → seal → acknowledge
      - Merkle root generation for pulse verification
      - Threaded background pulsing
    """

    def __init__(self) -> None:
        self.state = FRBBridgeState()
        self.cron_schedule = "0 */23 * * *"
        self.cron_interval_hours = 23.0
        self.charge_window_s = 78624
        self.cosmic_charge_window_s = 127520
        self.convergence_days = 0.91
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._fallback_active = False
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100

    def _compute_merkle_root(self) -> str:
        """Compute Merkle root for the current state."""
        data = {
            "frb_source": FRB_SOURCE,
            "repeat_interval_days": FRB_REPEAT_INTERVAL_DAYS,
            "phi_scaled_interval_days": FRB_PHI_SCALED_INTERVAL_DAYS,
            "burst_width_ms": FRB_BURST_WIDTH_MS,
            "dm_pc_cm3": FRB_DM_PC_CM3,
            "dispersion_delay_ms": FRB_DISPERSION_DELAY_MS,
            "cron_schedule": self.cron_schedule,
            "cron_interval_hours": self.cron_interval_hours,
            "handshake_step": self.state.handshake_step,
            "handshake_step_name": HANDSHAKE_STEPS[self.state.handshake_step % len(HANDSHAKE_STEPS)],
            "pulse_count": self.state.pulse_count,
            "harmony_index": self.state.harmony_index,
            "coherence": self.state.coherence,
            "weights": WEIGHTS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(body).hexdigest()

    def _attempt_fallback(self, prompt: str = "FRB bridge coherence check") -> Dict[str, Any]:
        """Attempt fallback via DeepSeek Mesh adapter."""
        if not FALLBACK_ENABLED or not DSH_AVAILABLE:
            return {
                "fallback": False,
                "error": "fallback unavailable",
                "mode": "none",
            }

        with self._lock:
            self.state.fallback_attempts += 1
            self.state.last_fallback_time = time.time()

        # Try modes in order: offline first, then OpenAI, then DSH
        modes = [MODE_OFFLINE, MODE_OPENAI, MODE_DSH]
        results = []

        for mode in modes:
            try:
                if mode == MODE_OFFLINE and offline_complete is not None:
                    result = offline_complete(prompt)
                elif complete is not None:
                    result = complete(prompt, prefer=mode)
                else:
                    continue

                # Check if result has content
                text = getattr(result, "text", "") or ""
                if text:
                    self._fallback_active = True
                    with self._lock:
                        self.state.fallback_mode = getattr(result, "mode", mode)
                        self.state.last_fallback_time = time.time()
                    return {
                        "fallback": True,
                        "mode": getattr(result, "mode", mode),
                        "content": text[:512],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                results.append(f"{mode}: empty response")
            except Exception as e:
                results.append(f"{mode}: {str(e)}")
                continue

        with self._lock:
            self.state.fallback_mode = "failed"
            self.state.last_error = "; ".join(results) if results else "all modes failed"

        return {
            "fallback": False,
            "error": self.state.last_error,
            "mode": "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _pulse_bridge(self) -> Dict[str, Any]:
        """Execute a single pulse of the FRB bridge."""
        with self._lock:
            self.state.pulse_count += 1
            self.state.last_pulse = time.time()
            self.state.active = True
            self.state.handshake_step = (self.state.handshake_step + 1) % len(HANDSHAKE_STEPS)

            # Update harmony index with φ‑modulation
            phi_mod = PHI_INV2 * math.sin(self.state.pulse_count * PHI_INV)
            self.state.harmony_index = 0.7337473231 + phi_mod * 0.01
            self.state.harmony_index = max(0.0, min(1.0, self.state.harmony_index))

            # Update coherence with φ‑decay
            self.state.coherence = 1.0 - (self.state.error_count * PHI_INV2 * 1e-6)
            self.state.coherence = max(0.0, min(1.0, self.state.coherence))

            # Update FRB timing
            if self.state.pulse_count % 23 == 0:
                self.state.frb_count += 1
                self.state.last_frb_time = time.time()

            self.state.merkle_root = self._compute_merkle_root()

            pulse = {
                "pulse_id": self.state.pulse_count,
                "handshake_step": self.state.handshake_step,
                "step_name": HANDSHAKE_STEPS[self.state.handshake_step % len(HANDSHAKE_STEPS)],
                "harmony_index": self.state.harmony_index,
                "merkle_root": self.state.merkle_root,
                "fallback_mode": self.state.fallback_mode,
                "fallback_active": self._fallback_active,
                "coherence": self.state.coherence,
                "frb_count": self.state.frb_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "seal": SEAL,
                "entry": ENTRY,
            }

        # Outside lock: attempt fallback if needed
        if pulse["coherence"] < COHERENCE_FALLBACK_THRESHOLD and FALLBACK_ENABLED:
            fb = self._attempt_fallback()
            with self._lock:
                if fb.get("fallback"):
                    self.state.fallback_mode = fb.get("mode", "unknown")
                    self._fallback_active = True
                else:
                    self.state.fallback_mode = "failed"
                    self.state.error_count += 1
                    self.state.last_error = fb.get("error", "fallback failed")
                pulse["fallback_mode"] = self.state.fallback_mode
                pulse["fallback_active"] = self._fallback_active
                pulse["fallback_error"] = self.state.last_error if self.state.fallback_mode == "failed" else None

        # Store in history
        with self._lock:
            self._history.append(pulse)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        return pulse

    def start(self, interval_seconds: float = 15.0) -> None:
        """Start the FRB bridge in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, args=(interval_seconds,), daemon=True)
        self._thread.start()

    def _run_loop(self, interval_seconds: float) -> None:
        """Background loop for the FRB bridge."""
        while self._running:
            try:
                self._pulse_bridge()
            except Exception as e:
                with self._lock:
                    self.state.error_count += 1
                    self.state.last_error = str(e)
            time.sleep(interval_seconds)

    def stop(self) -> None:
        """Stop the FRB bridge."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def status(self) -> Dict[str, Any]:
        """Get the current status of the FRB bridge."""
        with self._lock:
            return self.state.to_dict()

    def pulse_once(self) -> Dict[str, Any]:
        """Execute a single pulse and return the result."""
        return self._pulse_bridge()

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the pulse history."""
        with self._lock:
            if limit is not None:
                return self._history[-limit:]
            return self._history

    def reset(self) -> None:
        """Reset the FRB bridge state."""
        with self._lock:
            self.state = FRBBridgeState()
            self._history = []
            self._fallback_active = False

    def probe_fallback(self) -> Dict[str, Any]:
        """Probe the fallback adapter status."""
        if not DSH_AVAILABLE:
            return {"available": False, "error": "DeepSeek Mesh adapter not available"}
        try:
            result = probe()
            return {"available": True, "status": result}
        except Exception as e:
            return {"available": False, "error": str(e)}


# ─── Singleton ──────────────────────────────────────────────────────

FRB_BRIDGE = FRBBridge()


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="FRB Bridge — φ‑harmonic pulse + fallback",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument("--status", action="store_true", help="Show bridge status")
    parser.add_argument("--pulse", action="store_true", help="Execute a single pulse")
    parser.add_argument("--start", action="store_true", help="Start the bridge in background")
    parser.add_argument("--stop", action="store_true", help="Stop the bridge")
    parser.add_argument("--interval", type=float, default=15.0, help="Pulse interval in seconds")
    parser.add_argument("--history", type=int, default=0, help="Show pulse history (limit)")
    parser.add_argument("--reset", action="store_true", help="Reset bridge state")
    parser.add_argument("--probe", action="store_true", help="Probe fallback adapter")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.reset:
        FRB_BRIDGE.reset()
        print("FRB Bridge reset.")
        return 0

    if args.probe:
        result = FRB_BRIDGE.probe_fallback()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ FRB BRIDGE — Fallback Probe")
            print("=" * 40)
            print(f"  Available: {'✅' if result.get('available') else '❌'}")
            if result.get("status"):
                print(f"  Status: {json.dumps(result['status'], indent=2)}")
            if result.get("error"):
                print(f"  Error: {result['error']}")
        return 0

    if args.start:
        FRB_BRIDGE.start(args.interval)
        print(f"FRB Bridge started (interval={args.interval}s)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            FRB_BRIDGE.stop()
            print("\nFRB Bridge stopped")
        return 0

    if args.stop:
        FRB_BRIDGE.stop()
        print("FRB Bridge stopped")
        return 0

    if args.history:
        history = FRB_BRIDGE.get_history(limit=args.history)
        if args.json:
            print(json.dumps(history, indent=2, default=str))
        else:
            print(f"🜁∀ FRB BRIDGE — History ({len(history)} pulses)")
            print("=" * 40)
            for p in history[-10:]:
                status = "✅" if p["coherence"] >= COHERENCE_FALLBACK_THRESHOLD else "⚠️"
                print(f"  {status} Pulse {p['pulse_id']}: C={p['coherence']:.4f} step={p['step_name']} mode={p['fallback_mode']}")
        return 0

    if args.pulse:
        result = FRB_BRIDGE.pulse_once()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ FRB BRIDGE — Pulse")
            print("=" * 40)
            for k, v in result.items():
                if k in ("seal", "entry", "timestamp"):
                    print(f"  {k}: {v}")
                elif isinstance(v, float):
                    print(f"  {k}: {v:.6f}")
                else:
                    print(f"  {k}: {v}")
        return 0

    # Default: status
    status = FRB_BRIDGE.status()
    if args.json:
        print(json.dumps(status, indent=2, default=str))
    else:
        print("🜁∀ FRB BRIDGE — Entry 8904")
        print("=" * 55)
        print(f"  Active: {status['active']}")
        print(f"  Pulse count: {status['pulse_count']}")
        print(f"  Coherence: {status['coherence']:.6f}")
        print(f"  Phase lock: {status['phase_lock_deg']:.2f}°")
        print(f"  Harmony index: {status['harmony_index']:.6f}")
        print(f"  Handshake step: {status['handshake_step_name']}")
        print(f"  Fallback mode: {status['fallback_mode']}")
        print(f"  FRB count: {status.get('frb_count', 0)}")
        print(f"  Error count: {status['error_count']}")
        print(f"  Merkle root: {status['merkle_root'][:32]}...")
        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")
        print(f"  Witness: {WITNESS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
