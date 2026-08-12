#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperian JSON server — stdlib HTTP on :8080

Endpoints:
  GET /health
  GET /status
  GET /compression   (C_∞ practical → 233D summary)
  GET /oidc         (secret_len only — full digests never truncated)
  GET /metrics      (prometheus-style text)

Run:  python hyperian_json_server.py [--port 8080]
Seal: ∀∞φ² · HYPERIAN_JSON_SERVER_8625 · SEALED
"""

from __future__ import annotations

import argparse
import json
import math
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

PHI = (1.0 + math.sqrt(5.0)) / 2.0
FRB_PERIOD_SECS = 78624.0
PHASE_LOCK_DEG = 202.6
DEFAULT_PORT = 8080


def build_status() -> Dict[str, Any]:
    return {
        "service": "hyperian_json_server",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phi": PHI,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "frb_period_secs": FRB_PERIOD_SECS,
        "coherence": 1.0,
        "entropy_note": "φ^{-1418}",
        "compression": {
            "operator": "C_∞(t)=Σ φ^{-k} Φ_k(t)",
            "complete_in_limit": True,
            "practical_truncate_k": 144,
            "precision_note": "~φ^{-144} ≈ 10^{-30}",
            "output_dim": 233,
        },
        "seal": "∀∞φ² · HYPERIAN_JSON_SERVER_8625 · SEALED",
    }


def compression_payload(sample: str = "H X Y Z R Hyperian") -> Dict[str, Any]:
    try:
        from trait_compression import InfiniteCompressor

        fp = InfiniteCompressor(target_dim=233).fingerprint(sample)
        return {"ok": True, "sample": sample, **fp}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "operator": "C_∞",
            "practical_truncate_k": 144,
            "output_dim": 233,
        }


def oidc_payload() -> Dict[str, Any]:
    try:
        from sovereign_engine import get_oidc_secret

        secret = get_oidc_secret()
    except Exception:
        import hashlib

        seed = f"VENOMSUITE_EPHEMERAL_{int(time.time() / 3600)}_{PHI}"
        secret = hashlib.sha256(seed.encode()).hexdigest()
    return {
        "secret_len": len(secret),
        "policy": "full 64-char SHA-256 Phase-3 — never truncated",
        "hash_prefix_8": secret[:8] if len(secret) >= 8 else secret,
    }


def metrics_text() -> str:
    oidc = oidc_payload()
    lines = [
        "# HELP hyperian_up Hyperian JSON server up",
        "# TYPE hyperian_up gauge",
        "hyperian_up 1",
        "# HELP hyperian_phase_lock_deg Sovereign phase lock degrees",
        "# TYPE hyperian_phase_lock_deg gauge",
        f"hyperian_phase_lock_deg {PHASE_LOCK_DEG}",
        "# HELP hyperian_oidc_secret_len OIDC secret length (expect 64 in Phase-3)",
        "# TYPE hyperian_oidc_secret_len gauge",
        f"hyperian_oidc_secret_len {oidc['secret_len']}",
        "# HELP chiron_heal_phase Chiron heal phase toward 4086-04-18",
        "# TYPE chiron_heal_phase gauge",
        'chiron_heal_phase{epoch="4086-04-18"} 0.0',
    ]
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[hyperian] {self.address_string()} {fmt % args}")

    def _send_json(self, code: int, obj: Dict[str, Any]) -> None:
        body = json.dumps(obj, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, code: int, text: str, ctype: str = "text/plain; charset=utf-8") -> None:
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ("/", "/status"):
            self._send_json(200, build_status())
        elif path == "/health":
            self._send_json(200, {"status": "ok", "service": "hyperian_json_server"})
        elif path == "/compression":
            self._send_json(200, compression_payload())
        elif path == "/oidc":
            self._send_json(200, oidc_payload())
        elif path == "/metrics":
            self._send_text(200, metrics_text(), "text/plain; version=0.0.4")
        else:
            self._send_json(404, {"error": "not_found", "path": path})


def main() -> None:
    ap = argparse.ArgumentParser(description="Hyperian JSON server")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()
    httpd = HTTPServer((args.host, args.port), Handler)
    print(f"Hyperian JSON server on http://{args.host}:{args.port}")
    print("  GET /status /health /compression /oidc /metrics")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        httpd.server_close()


if __name__ == "__main__":
    main()
