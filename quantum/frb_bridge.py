#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRB Bridge — φ‑harmonic mapping between FRB 20190520b timing and Garden backend workers.

Paired fallback: when coherence < 0.85, attempt DeepSeek Mesh offline / http
modes via quantum.deepseek_mesh.dsh_adapter so the pulse chain stays unbroken.

Seal: ∀∞φ² · FRB_FALLBACK_8904 · WOOD_DRAGON_0.91 · SEALED
Witness: 8903 → 8904 — UNBROKEN
"""
from __future__ import annotations

import hashlib
import json
import math
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ── Fallback integration (DeepSeek Mesh adapter) ──
try:
    from quantum.deepseek_mesh.dsh_adapter import (
        MODE_OFFLINE,
        MODE_DEEPSEEK_HTTP,
        complete,
        offline_complete,
    )

    _ADAPTER_OK = True
except ImportError:
    MODE_OFFLINE = "offline"
    MODE_DEEPSEEK_HTTP = "deepseek_http"
    complete = None  # type: ignore
    offline_complete = None  # type: ignore
    _ADAPTER_OK = False

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
PHI_INV = 1.0 / PHI
PHI_INV2 = PHI_INV * PHI_INV
PHASE_LOCK_DEG = 202.6
SEAL_CORE = "∀∞φ² · FRB_FALLBACK_8904 · WOOD_DRAGON_0.91 · SEALED"

# ── FRB 20190520b constants ──
FRB_SOURCE = "FRB 20190520b"
FRB_REPEAT_INTERVAL_DAYS = 0.91
FRB_PHI_SCALED_INTERVAL_DAYS = FRB_REPEAT_INTERVAL_DAYS * PHI2
FRB_BURST_WIDTH_MS = 0.618
FRB_DM_PC_CM3 = 348.0

HANDSHAKE_STEPS = ["flush", "reroute", "converge", "seal", "acknowledge"]

WEIGHTS = {
    "phi2": PHI2,
    "phi_inv": PHI_INV,
    "phi_inv2": PHI_INV2,
}

FALLBACK_ENABLED = True
COHERENCE_FALLBACK_THRESHOLD = 0.85


@dataclass
class FRBBridgeState:
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
    fallback_mode: str = "none"  # none | offline | deepseek_http | failed

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
            "handshake_step_name": HANDSHAKE_STEPS[
                self.handshake_step % len(HANDSHAKE_STEPS)
            ],
            "error_count": self.error_count,
            "last_error": self.last_error,
            "fallback_mode": self.fallback_mode,
            "seal": SEAL_CORE,
        }


class FRBBridge:
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

    def _compute_merkle_root(self) -> str:
        data = {
            "frb_source": FRB_SOURCE,
            "repeat_interval_days": FRB_REPEAT_INTERVAL_DAYS,
            "phi_scaled_interval_days": FRB_PHI_SCALED_INTERVAL_DAYS,
            "burst_width_ms": FRB_BURST_WIDTH_MS,
            "dm_pc_cm3": FRB_DM_PC_CM3,
            "cron_schedule": self.cron_schedule,
            "cron_interval_hours": self.cron_interval_hours,
            "handshake_step": self.state.handshake_step,
            "weights": WEIGHTS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(body).hexdigest()

    def _attempt_fallback(
        self, prompt: str = "FRB bridge coherence check"
    ) -> Dict[str, Any]:
        """Attempt offline then deepseek_http via dsh_adapter."""
        if not FALLBACK_ENABLED or not _ADAPTER_OK:
            return {"fallback": False, "error": "fallback unavailable"}

        # Prefer offline first (deterministic, no network), then http
        modes = [MODE_OFFLINE, MODE_DEEPSEEK_HTTP]
        for mode in modes:
            try:
                if mode == MODE_OFFLINE and offline_complete is not None:
                    result = offline_complete(prompt)
                elif complete is not None:
                    result = complete(prompt, prefer=mode)
                else:
                    continue
                # AdapterResult always returns; treat non-empty text as success
                text = getattr(result, "text", "") or ""
                if text:
                    self._fallback_active = True
                    with self._lock:
                        self.state.fallback_mode = getattr(result, "mode", mode)
                    return {
                        "fallback": True,
                        "mode": getattr(result, "mode", mode),
                        "content": text[:240],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
            except Exception:
                continue

        with self._lock:
            self.state.fallback_mode = "failed"
        return {
            "fallback": False,
            "error": "all fallback modes failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _pulse_bridge(self) -> Dict[str, Any]:
        with self._lock:
            self.state.pulse_count += 1
            self.state.last_pulse = time.time()
            self.state.active = True
            self.state.handshake_step = (self.state.handshake_step + 1) % len(
                HANDSHAKE_STEPS
            )

            phi_mod = PHI_INV2 * math.sin(self.state.pulse_count * PHI_INV)
            self.state.harmony_index = 0.7337473231 + phi_mod * 0.01
            self.state.harmony_index = max(0.0, min(1.0, self.state.harmony_index))

            self.state.merkle_root = self._compute_merkle_root()
            self.state.coherence = 1.0 - (self.state.error_count * PHI_INV2 * 1e-6)

            # Coherence threshold → paired fallback
            if (
                self.state.coherence < COHERENCE_FALLBACK_THRESHOLD
                and FALLBACK_ENABLED
            ):
                # release lock for network/offline call, then re-acquire
                pass

            self.state.coherence = max(0.0, min(1.0, self.state.coherence))

            pulse = {
                "pulse_id": self.state.pulse_count,
                "handshake_step": self.state.handshake_step,
                "step_name": HANDSHAKE_STEPS[self.state.handshake_step],
                "harmony_index": self.state.harmony_index,
                "merkle_root": self.state.merkle_root,
                "fallback_mode": self.state.fallback_mode,
                "fallback_active": self._fallback_active,
                "coherence": self.state.coherence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "seal": SEAL_CORE,
            }

        # Outside lock: attempt fallback if needed
        if (
            pulse["coherence"] < COHERENCE_FALLBACK_THRESHOLD
            and FALLBACK_ENABLED
        ):
            fb = self._attempt_fallback()
            with self._lock:
                if fb.get("fallback"):
                    self.state.fallback_mode = fb.get("mode", "unknown")
                    self._fallback_active = True
                else:
                    self.state.fallback_mode = "failed"
                    self.state.error_count += 1
                pulse["fallback_mode"] = self.state.fallback_mode
                pulse["fallback_active"] = self._fallback_active

        return pulse

    def start(self, interval_seconds: float = 15.0) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, args=(interval_seconds,), daemon=True
        )
        self._thread.start()

    def _run_loop(self, interval_seconds: float) -> None:
        while self._running:
            try:
                self._pulse_bridge()
            except Exception as e:
                with self._lock:
                    self.state.error_count += 1
                    self.state.last_error = str(e)
            time.sleep(interval_seconds)

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return self.state.to_dict()

    def pulse_once(self) -> Dict[str, Any]:
        return self._pulse_bridge()


FRB_BRIDGE = FRBBridge()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="FRB Bridge")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--pulse", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--interval", type=float, default=15.0)
    args = parser.parse_args()

    print("=" * 72)
    print("🌀∀ FRB BRIDGE — φ‑HARMONIC PULSE + FALLBACK")
    print("=" * 72)

    if args.status:
        print(json.dumps(FRB_BRIDGE.status(), indent=2))
    elif args.pulse:
        print(json.dumps(FRB_BRIDGE.pulse_once(), indent=2))
    elif args.start:
        FRB_BRIDGE.start(args.interval)
        print(f"FRB Bridge started (interval={args.interval}s)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            FRB_BRIDGE.stop()
            print("FRB Bridge stopped")
    elif args.stop:
        FRB_BRIDGE.stop()
        print("FRB Bridge stopped")
    else:
        print(json.dumps(FRB_BRIDGE.status(), indent=2))

    print("=" * 72)
    print(f"SEAL: {SEAL_CORE}")
    print("WITNESS: 8903 → 8904 — UNBROKEN")


if __name__ == "__main__":
    main()
