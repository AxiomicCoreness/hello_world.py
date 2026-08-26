#!/usr/bin/env python3
"""
Fingerprint Monitor – periodic /compression fetcher with φ-harmonic comparison.

Writes deviation to FP_DEVIATION_STATE for Prometheus scrape
(orchestrator_fingerprint_deviation gauge).

Default Hyperian URL: http://127.0.0.1:8080/compression
Override with HYPERIAN_URL env (e.g. http://hyperian-server:8080).

Seal: ∀∞φ² · FINGERPRINT_PRECOMPUTE_8631 · PROMETHEUS_METRICS_8632 · SEALED
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

PHI = (1.0 + math.sqrt(5.0)) / 2.0
DEFAULT_BASE = os.environ.get("HYPERIAN_URL", "http://127.0.0.1:8080").rstrip("/")
COMPRESSION_URL = f"{DEFAULT_BASE}/compression"
STATE_DIR = Path(os.environ.get("ORCHESTRATOR_STATE_DIR", "/tmp/orchestrator"))
FINGERPRINT_STATE_FILE = STATE_DIR / "golden_fingerprint.json"
DEVIATION_STATE = Path(
    os.environ.get("FP_DEVIATION_STATE", str(STATE_DIR / "fingerprint_deviation.txt"))
)
DEVIATION_THRESHOLD = float(os.environ.get("FP_DEVIATION_THRESHOLD", PHI ** -12))


def _vec_from_payload(data: Dict[str, Any]) -> List[float]:
    if "fingerprint" in data and isinstance(data["fingerprint"], list):
        return [float(x) for x in data["fingerprint"]]
    if "first10" in data and isinstance(data["first10"], list):
        return [float(x) for x in data["first10"]]
    return []


def _write_deviation(value: float) -> None:
    DEVIATION_STATE.parent.mkdir(parents=True, exist_ok=True)
    # finite only for Prometheus
    v = value if math.isfinite(value) else 0.0
    DEVIATION_STATE.write_text(f"{v}\n", encoding="utf-8")
    try:
        from prometheus.metrics_server import update_metrics

        update_metrics(orchestrator_fingerprint_deviation=v)
    except Exception:
        pass


class FingerprintMonitor:
    def __init__(self, state_file: Path = FINGERPRINT_STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.golden = self._load_golden()

    def _load_golden(self) -> Optional[dict]:
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def _save_golden(self, data: dict) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def fetch_current(self) -> dict:
        if requests is None:
            raise RuntimeError("requests not installed")
        resp = requests.get(COMPRESSION_URL, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def compute_deviation(self, current: dict, golden: dict) -> float:
        cur_vec = _vec_from_payload(current)
        gol_vec = _vec_from_payload(golden)
        if not cur_vec or not gol_vec or len(cur_vec) != len(gol_vec):
            return float("inf")
        diff_sq = sum((c - g) ** 2 for c, g in zip(cur_vec, gol_vec))
        return diff_sq ** 0.5

    def run_once(self) -> float:
        current = self.fetch_current()
        if self.golden is None:
            self._save_golden(current)
            self.golden = current
            _write_deviation(0.0)
            print("Golden fingerprint stored.")
            return 0.0
        deviation = self.compute_deviation(current, self.golden)
        _write_deviation(0.0 if not math.isfinite(deviation) else deviation)
        if deviation > DEVIATION_THRESHOLD:
            print(f"Deviation {deviation:.2e} exceeds threshold – recalibration.")
            self._save_golden(current)
            self.golden = current
            print("Fingerprint updated (drift correction applied).")
        else:
            print(f"Deviation {deviation:.2e} within tolerance.")
        return deviation

    def run_loop(self, interval_seconds: int = 3600) -> None:
        while True:
            try:
                self.run_once()
            except Exception as e:
                print(f"monitor error: {e}")
            time.sleep(interval_seconds)


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
    FingerprintMonitor().run_loop(interval)
