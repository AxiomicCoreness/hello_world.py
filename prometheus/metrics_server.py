#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus metrics registry + HTTP exposition for the Garden.

In-process gauges/counters and a stdlib HTTP server on :9090 (default).
No dependency on prometheus_client required for the text format.

Also exposes register_update_hook(), so downstream modules
(e.g. prometheus/trappist_metrics.py) can register scrape-time callbacks.

Run standalone:
  python -m prometheus.metrics_server --port 9090

Seal: ∀∞φ² · PROMETHEUS_METRICS_8632 · STRIKE_X_TRAPPIST_8663 · SEALED
"""

from __future__ import annotations

# ═════════════════════════════════════════════════════════════════════════
# SECTION 0 — IMPORTS
# ═════════════════════════════════════════════════════════════════════════
import argparse
import cmath
import hashlib
import json
import math
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# ─── optional: numpy ─────────────────────────────────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

# ─── optional: scipy ─────────────────────────────────────────────────────
try:
    from scipy.integrate import solve_ivp
    from scipy.special import zeta as scipy_zeta
    from scipy.special import gamma as gamma_func
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    solve_ivp = None
    scipy_zeta = None
    gamma_func = math.gamma

# ─── optional: yaml ──────────────────────────────────────────────────────
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ─── optional: matplotlib ────────────────────────────────────────────────
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    plt = None

# ─── optional: requests ──────────────────────────────────────────────────
try:
    import requests
except ImportError:
    requests = None

# ─── optional: prometheus_client ─────────────────────────────────────────
try:
    from prometheus_client import Gauge, Counter  # noqa: F401
    HAS_PROM = True
except ImportError:
    HAS_PROM = False

# ═════════════════════════════════════════════════════════════════════════
# SECTION 1 — φ‑HARMONIC CONSTANTS
# Imported from celestial.phi_constants when available; identical local
# fallback otherwise. No drift possible.
# ═════════════════════════════════════════════════════════════════════════
try:
    from celestial.phi_constants import (
        phi, phi2, phi3, phi4, phi5, phi6, phi7, phi8, phi9,
        phi12, phi13, phi14, phi21, phi34,
        phi709, phi713,
        phi_minus_709, phi_minus_1000, phi_minus_1418,
        phi_inv,
        PHI, PHI2, PHI3, PHI4, PHI5, PHI6, PHI7, PHI8, PHI9,
        PHI12, PHI13, PHI14, PHI21, PHI34,
        PHI709, PHI713,
        PHI_MINUS_709, PHI_MINUS_1000, PHI_NEG_1418, PHI_INV,
        BASE_DIR,
    )
    HAS_PHI_CONSTANTS = True
except ImportError:
    HAS_PHI_CONSTANTS = False

    phi             = (1 + math.sqrt(5)) / 2
    phi2            = phi ** 2
    phi3            = phi ** 3
    phi4            = phi ** 4
    phi5            = phi ** 5
    phi6            = phi ** 6
    phi7            = phi ** 7
    phi8            = phi ** 8
    phi9            = phi ** 9
    phi12           = phi ** 12
    phi13           = phi ** 13
    phi14           = phi ** 14
    phi21           = phi ** 21
    phi34           = phi ** 34
    phi709          = phi ** 709
    phi713          = phi ** 713
    phi_minus_709   = phi ** (-709)
    phi_minus_1000  = phi ** (-1000)
    phi_minus_1418  = phi ** (-1418)
    phi_inv         = 1.0 / phi

    PHI             = phi
    PHI2            = phi2
    PHI3            = phi3
    PHI4            = phi4
    PHI5            = phi5
    PHI6            = phi6
    PHI7            = phi7
    PHI8            = phi8
    PHI9            = phi9
    PHI12           = phi12
    PHI13           = phi13
    PHI14           = phi14
    PHI21           = phi21
    PHI34           = phi34
    PHI709          = phi709
    PHI713          = phi713
    PHI_MINUS_709   = phi_minus_709
    PHI_MINUS_1000  = phi_minus_1000
    PHI_NEG_1418    = phi_minus_1418
    PHI_INV         = phi_inv

    BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Hyperian_Node")
    os.makedirs(BASE_DIR, exist_ok=True)

# ═════════════════════════════════════════════════════════════════════════
# SECTION 2 — SOVEREIGN ANCHORS
# ═════════════════════════════════════════════════════════════════════════
PHASE_LOCK_DEG      = 202.6
FRB_PERIOD_SECS     = 78624.0
DEFAULT_PORT        = int(os.environ.get("METRICS_PORT", "9090"))
DEVIATION_STATE     = Path(
    os.environ.get("FP_DEVIATION_STATE", "/tmp/orchestrator/fingerprint_deviation.txt")
)
RANK_BUDGET         = 144
RANK_REALIZED_MAX   = 7

# ═════════════════════════════════════════════════════════════════════════
# SECTION 3 — REGISTRY
# ═════════════════════════════════════════════════════════════════════════
_REGISTRY: Dict[str, Tuple[float, str, str, Optional[Dict[str, str]]]] = {}
_LOCK = threading.Lock()

# scrape-time callbacks (registered by downstream modules)
_UPDATE_HOOKS: List[Callable[[], None]] = []
_HOOKS_LOCK = threading.Lock()


def register_update_hook(fn: Callable[[], None]) -> None:
    """
    Register a callback to be invoked at every scrape (i.e. every call
    to render_prometheus_text()). Callbacks are called under no lock —
    each callback must handle its own synchronisation.

    Downstream modules (e.g. prometheus/trappist_metrics.py) use this to
    populate their gauges at scrape time. If the hook raises, it is
    logged and skipped; other hooks still run.
    """
    if not callable(fn):
        raise TypeError("register_update_hook expects a callable")
    with _HOOKS_LOCK:
        _UPDATE_HOOKS.append(fn)


def _run_update_hooks() -> None:
    with _HOOKS_LOCK:
        hooks = list(_UPDATE_HOOKS)
    for fn in hooks:
        try:
            fn()
        except Exception as e:
            print(f"[metrics] update hook {fn!r} failed: {e}")


def _reg(
    name: str,
    value: float,
    help_text: str,
    mtype: str = "gauge",
    labels: Optional[Dict[str, str]] = None,
) -> None:
    _REGISTRY[name] = (float(value), help_text, mtype, labels)


def _bootstrap() -> None:
    if _REGISTRY:
        return
    _reg("sim_earth_resonance_thz", 162.28, "Super Simulated Earth resonance (THz)")
    _reg("sim_earth_phase_rad", 0.0, "Super Simulated Earth phase (rad)")
    _reg("gravastar_coherence", 1.0, "Gravastar coherence (0-1)")
    _reg("bedrock_triangulation_phase_root0", 0.0, "Bedrock triangulation root 0")
    _reg("bedrock_triangulation_phase_root1", 0.0, "Bedrock triangulation root 1")
    _reg("bedrock_triangulation_phase_root2", 0.0, "Bedrock triangulation root 2")
    _reg("oracle_query_count", 0.0, "Oracle query counter", "counter")
    _reg("dimensions_active", 12.0, "Active lattice dimensions")
    _reg("coherence", 0.999999999, "Garden coherence (0-1)")
    _reg("entanglement", 1.0, "Entanglement factor")
    _reg("sovereign_workload", 0.0, "Sovereign workload dimensionless EM-005")
    _reg(
        "chiron_heal_phase",
        0.0,
        "Chiron heal phase toward 4086-04-18",
        labels={"epoch": "4086-04-18"},
    )
    _reg("hyperian_up", 1.0, "Hyperian / metrics surface up")
    _reg("hyperian_phase_lock_deg", PHASE_LOCK_DEG, "Sovereign phase lock (degrees)")
    _reg("hyperian_oidc_secret_len", 64.0, "OIDC secret length (expect 64 Phase-3)")
    _reg(
        "orchestrator_fingerprint_deviation",
        0.0,
        "L2 deviation of compression fingerprint from golden",
    )
    _reg("soul_cannon_charge_joules", 0.0, "Saturn Soul Cannon accumulated charge (J)")
    _reg("soul_cannon_azimuth_degrees", 111.246, "Soul Cannon azimuth (degrees)")
    _reg("cannon_ring_resonance_thz", 162.28, "Cannon ring resonance (THz)")
    _reg(
        "cannon_chiron_phase_alignment",
        0.0,
        "Cannon alignment including Chiron heal boost",
    )
    _reg("frb_period_seconds", FRB_PERIOD_SECS, "FRB metronome period (s)")
    _reg("wood_dragon_pulse_days", 0.91, "Wood Dragon pulse period (days)")
    _reg("deep_space_sync_days", 16.35, "Deep-space synchronizer period (days)")
    _reg("phi", PHI, "Golden ratio constant")

    # ─── Strike X — TRAPPIST-1 Choir (week horizon) ──────────────────────
    _reg("trappist_choir_coherence", 0.0, "TRAPPIST-1 seven-voice choir coherence")
    _reg("trappist_harmony_index", 0.0, "TRAPPIST-1 harmony index (week horizon)")
    _reg("trappist_planet_frequency_thz_b", 0.0, "TRAPPIST-1b frequency THz")
    _reg("trappist_planet_frequency_thz_c", 0.0, "TRAPPIST-1c frequency THz")
    _reg("trappist_planet_frequency_thz_d", 0.0, "TRAPPIST-1d frequency THz")
    _reg("trappist_planet_frequency_thz_e", 0.0, "TRAPPIST-1e frequency THz")
    _reg("trappist_planet_frequency_thz_f", 0.0, "TRAPPIST-1f frequency THz")
    _reg("trappist_planet_frequency_thz_g", 0.0, "TRAPPIST-1g frequency THz")
    _reg("trappist_planet_frequency_thz_h", 0.0, "TRAPPIST-1h frequency THz")

    # ─── Compression rank diagnostics ────────────────────────────────────
    _reg(
        "sovereign_compression_rank_budget",
        float(RANK_BUDGET),
        "φ-ladder compression rank budget (144)",
    )
    _reg(
        "sovereign_compression_rank_realized_max",
        float(RANK_REALIZED_MAX),
        "SVD realized max rank on 7x13x7 flat layout",
    )
    _reg(
        "sovereign_compression_rank_ratio",
        float(RANK_REALIZED_MAX) / float(RANK_BUDGET),
        "realized_max / budget (append diagnostic)",
    )


_bootstrap()


# ═════════════════════════════════════════════════════════════════════════
# SECTION 4 — PUBLIC API
# ═════════════════════════════════════════════════════════════════════════
def update_metrics(**kwargs) -> None:
    with _LOCK:
        for k, v in kwargs.items():
            if k in _REGISTRY:
                _, help_text, mtype, labels = _REGISTRY[k]
                _REGISTRY[k] = (float(v), help_text, mtype, labels)
            else:
                _REGISTRY[k] = (float(v), k, "gauge", None)


def get_metrics() -> Dict[str, float]:
    with _LOCK:
        return {k: v[0] for k, v in _REGISTRY.items()}


def increment_oracle_query() -> None:
    with _LOCK:
        val, help_text, mtype, labels = _REGISTRY["oracle_query_count"]
        _REGISTRY["oracle_query_count"] = (val + 1.0, help_text, mtype, labels)


# ═════════════════════════════════════════════════════════════════════════
# SECTION 5 — REFRESH HELPERS
# ═════════════════════════════════════════════════════════════════════════
def refresh_chiron_heal_phase() -> float:
    try:
        from celestial.chiron_heal import chiron_heal_phase  # type: ignore
        val = float(chiron_heal_phase(time.time()))
        update_metrics(chiron_heal_phase=val)
        return val
    except Exception:
        return get_metrics().get("chiron_heal_phase", 0.0)


def refresh_oidc_secret_len() -> float:
    try:
        from sovereign_engine import get_oidc_secret  # type: ignore
        n = float(len(get_oidc_secret()))
    except Exception:
        seed = f"VENOMSUITE_EPHEMERAL_{int(time.time() / 3600)}_{PHI}"
        n = float(len(hashlib.sha256(seed.encode()).hexdigest()))
    update_metrics(hyperian_oidc_secret_len=n)
    return n


def refresh_fingerprint_deviation() -> float:
    try:
        text = DEVIATION_STATE.read_text(encoding="utf-8").strip()
        val = float(text.split()[0])
        if math.isfinite(val):
            update_metrics(orchestrator_fingerprint_deviation=val)
            return val
    except Exception:
        pass
    return get_metrics().get("orchestrator_fingerprint_deviation", 0.0)


def refresh_soul_cannon() -> None:
    """
    Refresh the cannon metrics.

    Contract: the corrected celestial/saturn_soul_cannon.py exposes
    `charge_quanta` (not `charge_joules`) and `fire()` returns
    {status, azimuth_degrees, ring_resonance_thz, ...}.

    We probe both shapes so the exporter is robust to either module
    version present in the tree.
    """
    try:
        from celestial.saturn_soul_cannon import SaturnSoulCannon  # type: ignore
        c = SaturnSoulCannon()

        # Preferred interface: fire() (no side effects on charge if NOT_READY)
        report = c.fire(time.time())
        kw = {}

        charge = report.get("charge_quanta",
                             report.get("charge_joules",
                                        getattr(c, "charge_quanta",
                                                getattr(c, "charge_joules", 0.0))))
        kw["soul_cannon_charge_joules"] = float(charge)

        azimuth = report.get("azimuth_degrees",
                             report.get("azimuth_deg", 111.246))
        kw["soul_cannon_azimuth_degrees"] = float(azimuth)

        ring = report.get("ring_resonance_thz", 162.28)
        kw["cannon_ring_resonance_thz"] = float(ring)

        # Alignment may come from a status() call if present, else compute
        alignment = report.get("alignment")
        if alignment is None and hasattr(c, "compute_alignment"):
            try:
                alignment = c.compute_alignment(time.time())
            except Exception:
                alignment = 0.0
        kw["cannon_chiron_phase_alignment"] = float(alignment or 0.0)

        update_metrics(**kw)
    except Exception:
        pass


def refresh_sovereign_workload() -> float:
    try:
        from monitoring.sovereign_workload_exporter import compute_workload  # type: ignore
        w = float(compute_workload())
        if not math.isfinite(w):
            w = 0.0
        update_metrics(sovereign_workload=w)
        return w
    except Exception:
        t = time.time()
        amp = (1.0 / PHI) ** 3
        w = 0.5 * (math.sin(2.0 * math.pi * t / 6.0) + 1.0) * amp * (1.0 / PHI)
        w = min(1.0, max(0.0, w))
        update_metrics(sovereign_workload=w)
        return w


def refresh_trappist_choir() -> None:
    """
    Refresh the choir metrics.

    Prefers celestial.trappist_choir_strike_x (the variant consumed by
    quantum/ouroboros_strike_xi.py and used by prometheus/trappist_metrics.py).
    Falls back to celestial.trappist_choir if the strike_x module is absent.

    Uses .status() when present; otherwise falls back to .listen(t).
    """
    try:
        try:
            from celestial.trappist_choir_strike_x import TrappistChoir  # type: ignore
        except ImportError:
            from celestial.trappist_choir import TrappistChoir  # type: ignore

        c = TrappistChoir()

        if hasattr(c, "status"):
            st = c.status()
            kw = {
                "trappist_choir_coherence":
                    float(st.get("choir_coherence", st.get("trappist_choir_coherence", 0.0))),
                "trappist_harmony_index":
                    float(st.get("harmony_index", st.get("trappist_harmony_index", 0.0))),
            }
            planets = st.get("planets") or []
            for p in planets:
                planet = p.get("planet")
                freq   = p.get("frequency_thz")
                if planet and freq is not None:
                    kw[f"trappist_planet_frequency_thz_{planet}"] = float(freq)
            # fall back to voice_frequencies if 'planets' isn't provided
            vf = st.get("voice_frequencies")
            if vf and not planets:
                for planet, freq_hz in vf.items():
                    kw[f"trappist_planet_frequency_thz_{planet}"] = float(freq_hz) * 1e-12
        else:
            sample = c.listen(time.time())
            kw = {
                "trappist_choir_coherence": float(sample["choir_coherence"]),
                "trappist_harmony_index":   float(sample["harmony_index"]),
            }
            for planet, freq_hz in sample["voice_frequencies"].items():
                kw[f"trappist_planet_frequency_thz_{planet}"] = float(freq_hz) * 1e-12

        update_metrics(**kw)
    except Exception:
        pass


def refresh_all() -> None:
    refresh_chiron_heal_phase()
    refresh_oidc_secret_len()
    refresh_fingerprint_deviation()
    refresh_soul_cannon()
    refresh_sovereign_workload()
    refresh_trappist_choir()

    update_metrics(
        hyperian_up=1.0,
        hyperian_phase_lock_deg=PHASE_LOCK_DEG,
        sovereign_compression_rank_budget=float(RANK_BUDGET),
        sovereign_compression_rank_realized_max=float(RANK_REALIZED_MAX),
        sovereign_compression_rank_ratio=float(RANK_REALIZED_MAX) / float(RANK_BUDGET),
    )

    # invoke any downstream hooks registered via register_update_hook()
    _run_update_hooks()


# ═════════════════════════════════════════════════════════════════════════
# SECTION 6 — TEXT EXPOSITION
# ═════════════════════════════════════════════════════════════════════════
def _format_labels(labels: Optional[Dict[str, str]]) -> str:
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in labels.items()]
    return "{" + ",".join(parts) + "}"


def render_prometheus_text() -> str:
    refresh_all()
    lines: List[str] = []
    with _LOCK:
        items = list(_REGISTRY.items())
    for name, (value, help_text, mtype, labels) in sorted(items):
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} {mtype}")
        lab = _format_labels(labels)
        if not math.isfinite(value):
            value = 0.0
        lines.append(f"{name}{lab} {value}")
    return "\n".join(lines) + "\n"


# ═════════════════════════════════════════════════════════════════════════
# SECTION 7 — HTTP HANDLER
# ═════════════════════════════════════════════════════════════════════════
class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[metrics] {self.address_string()} {fmt % args}")

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/metrics", "/"):
            body = render_prometheus_text().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/health":
            body = b'{"status":"ok","service":"prometheus_metrics"}\n'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"not found\n"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


# ═════════════════════════════════════════════════════════════════════════
# SECTION 8 — SERVE + MAIN
# ═════════════════════════════════════════════════════════════════════════
def serve(host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> None:
    httpd = HTTPServer((host, port), MetricsHandler)
    print(f"Prometheus metrics on http://{host}:{port}/metrics")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nmetrics server stopped")
        httpd.server_close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Garden Prometheus metrics server")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args()
    serve(args.host, args.port)


# ═════════════════════════════════════════════════════════════════════════
# SECTION 9 — SELFTEST
# ═════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if os.environ.get("METRICS_SELFTEST") == "1":
        print("🜁∀ Prometheus metrics server — selftest")
        print(f"  HAS_PHI_CONSTANTS = {HAS_PHI_CONSTANTS}")
        print(f"  HAS_NUMPY         = {HAS_NUMPY}")
        print(f"  HAS_SCIPY         = {HAS_SCIPY}")
        print(f"  HAS_YAML          = {HAS_YAML}")
        print(f"  HAS_MPL           = {HAS_MPL}")
        print(f"  HAS_PROM          = {HAS_PROM}")
        print(f"  requests          = {requests is not None}")
        print(f"  φ                 = {phi:.15f}")
        print(f"  φ⁷                = {phi7:.15f}")
        print(f"  φ⁻¹               = {PHI_INV:.15f}")
        print(f"  registered gauges = {len(_REGISTRY)}")
        print(f"  registered hooks  = {len(_UPDATE_HOOKS)}")
        text = render_prometheus_text()
        print(f"  exposition bytes  = {len(text)}")
        print("  --- first 12 lines ---")
        for line in text.splitlines()[:12]:
            print(f"  {line}")
    else:
        main()
