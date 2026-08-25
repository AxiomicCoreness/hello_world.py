#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sovereign workload exporter — EM-005

Dimensionless gauge in [0, 1]. φ-harmonic smoothing (144-sample EMA).
Stdlib HTTP :9095/metrics — no prometheus_client required.
Never emits secrets.

Seal: ∀∞φ² · SOVEREIGN_WORKLOAD_8635 · EM005 · SEALED
"""

from __future__ import annotations

import argparse
import collections
import math
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Deque

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
T_PHI = 0.5983  # φ-pulse cycle (s)
WINDOW = 144
DEFAULT_PORT = 9095

_samples: Deque[float] = collections.deque(maxlen=WINDOW)


def raw_workload(t: float) -> float:
    # Oscillates 0..φ^{-3} with 6s period
    amp = PHI_INV ** 3
    return 0.5 * (math.sin(2.0 * math.pi * t / 6.0) + 1.0) * amp


def ema_phi(values: Deque[float]) -> float:
    if not values:
        return 0.0
    # φ^{-1} EMA weight toward recent samples
    alpha = PHI_INV
    acc = values[0]
    for v in list(values)[1:]:
        acc = alpha * v + (1.0 - alpha) * acc
    return min(1.0, max(0.0, acc))


def compute_workload() -> float:
    t = time.time()
    _samples.append(raw_workload(t))
    return ema_phi(_samples)


def metrics_text(value: float) -> str:
    return (
        "# HELP sovereign_workload Sovereign workload (dimensionless, EM-005)\n"
        "# TYPE sovereign_workload gauge\n"
        f"sovereign_workload {value}\n"
        "# HELP sovereign_workload_em em protocol label as gauge (005)\n"
        "# TYPE sovereign_workload_em gauge\n"
        "sovereign_workload_em{protocol=\"005\"} 5\n"
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[workload] {self.address_string()} {fmt % args}")

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/metrics", "/"):
            w = compute_workload()
            body = metrics_text(w).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/health":
            body = b'{"status":"ok","service":"sovereign_workload","em":"005"}\n'
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args()
    httpd = HTTPServer((args.host, args.port), Handler)
    print(f"sovereign_workload EM-005 on http://{args.host}:{args.port}/metrics")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        httpd.server_close()


if __name__ == "__main__":
    main()
