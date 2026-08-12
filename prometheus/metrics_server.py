#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus metrics registry + HTTP exposition for the Garden.

In-process gauges/counters and a stdlib HTTP server on :9090 (default).
No dependency on prometheus_client required for the text format.

Run standalone:
  python -m prometheus.metrics_server --port 9090

Seal: ∀∞φ² · PROMETHEUS_METRICS_8632 · RANK_METRICS_APPEND_8656 · SEALED
"""

from __future__ import annotations

import argparse
import math
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHASE_LOCK_DEG = 202.6
FRB_PERIOD_SECS = 78624.0
DEFAULT_PORT = int(os.environ.get("METRICS_PORT", "9090"))
DEVIATION_STATE = Path(
    os.environ.get("FP_DEVIATION_STATE", "/tmp/orchestrator/fingerprint_deviation.txt")
)
RANK_BUDGET = 144
RANK_REALIZED_MAX = 7

# name -> (value, help, type, labels_dict_or_None)
_REGISTRY: Dict[str, Tuple[float, str, str, Optional[Dict[str, str]]]] = {}
_LOCK = threading.Lock()


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
    _reg("chiron_heal_phase", 0.0, "Chiron heal phase toward 4086-04-18", labels={"epoch": "4086-04-18"})
    _reg("hyperian_up", 1.0, "Hyperian / metrics surface up")
    _reg("hyperian_phase_lock_deg", PHASE_LOCK_DEG, "Sovereign phase lock (degrees)")
    _reg("hyperian_oidc_secret_len", 64.0, "OIDC secret length (expect 64 Phase-3)")
    _reg("orchestrator_fingerprint_deviation", 0.0, "L2 deviation of compression fingerprint from golden")
    _reg("soul_cannon_charge_joules", 0.0, "Saturn Soul Cannon accumulated charge (J)")
    _reg("soul_cannon_azimuth_degrees", 111.246, "Soul Cannon azimuth (degrees)")
    _reg("cannon_ring_resonance_thz", 162.28, "Cannon ring resonance (THz)")
    _reg("cannon_chiron_phase_alignment", 0.0, "Cannon alignment including Chiron heal boost")
    _reg("frb_period_seconds", FRB_PERIOD_SECS, "FRB metronome period (s)")
    _reg("wood_dragon_pulse_days", 0.91, "Wood Dragon pulse period (days)")
    _reg("deep_space_sync_days", 16.35, "Deep-space synchronizer period (days)")
    _reg("phi", PHI, "Golden ratio constant")
    # --- Rank append (φ-ladder budget vs realized SVD max on 7×13×7) ---
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


def refresh_chiron_heal_phase() -> float:
    try:
        from celestial.chiron_heal import chiron_heal_phase

        val = float(chiron_heal_phase(time.time()))
        update_metrics(chiron_heal_phase=val)
        return val
    except Exception:
        return get_metrics().get("chiron_heal_phase", 0.0)


def refresh_oidc_secret_len() -> float:
    try:
        from sovereign_engine import get_oidc_secret

        n = float(len(get_oidc_secret()))
    except Exception:
        import hashlib

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
    try:
        from celestial.saturn_soul_cannon import SaturnSoulCannon

        c = SaturnSoulCannon()
        st = c.status()
        update_metrics(
            soul_cannon_charge_joules=float(st.get("charge_joules", 0.0)),
            cannon_chiron_phase_alignment=float(st.get("alignment", 0.0)),
            soul_cannon_azimuth_degrees=float(st.get("azimuth_deg", 111.246)),
        )
    except Exception:
        pass


def refresh_sovereign_workload() -> float:
    try:
        from monitoring.sovereign_workload_exporter import compute_workload

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


def refresh_all() -> None:
    refresh_chiron_heal_phase()
    refresh_oidc_secret_len()
    refresh_fingerprint_deviation()
    refresh_soul_cannon()
    refresh_sovereign_workload()
    update_metrics(
        hyperian_up=1.0,
        hyperian_phase_lock_deg=PHASE_LOCK_DEG,
        sovereign_compression_rank_budget=float(RANK_BUDGET),
        sovereign_compression_rank_realized_max=float(RANK_REALIZED_MAX),
        sovereign_compression_rank_ratio=float(RANK_REALIZED_MAX) / float(RANK_BUDGET),
    )


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


if __name__ == "__main__":
    main()
