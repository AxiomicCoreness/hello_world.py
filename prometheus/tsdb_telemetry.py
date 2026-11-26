# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)
# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)
# Design by Clarke Yoursa Tee
"""
prometheus/tsdb_telemetry.py — Continuous-to-discrete TSDB sampling, gauges,
monotonic counters with reset rule, StaleNaN lookback, and Grafana envelope projection.

Explicitly registers entanglement (for Panel 105) and excludes sovereign_workload.
"""
import math
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

DESIGN_CREDIT: str = "Design by Clarke Yoursa Tee"
DEFAULT_LOOKBACK_SEC: float = 300.0


def counter_delta(c_prev: float, c_curr: float) -> float:
    """Monotonic counter step with reset rule:
    delta+ = C[j] - C[j-1] if C[j] >= C[j-1] else C[j].
    """
    prev_val = float(c_prev)
    curr_val = float(c_curr)
    if prev_val < 0.0 or curr_val < 0.0:
        raise ValueError("Counter values must be non-negative")
    if curr_val >= prev_val:
        return curr_val - prev_val
    return curr_val


def counter_rate(
    samples: Sequence[Tuple[float, float]],
    t_a: float,
    t_b: float,
) -> float:
    """Rate estimator over window W = [t_a, t_b]: sum(delta+) / (t_b - t_a)."""
    dt = float(t_b) - float(t_a)
    if dt <= 0.0:
        raise ValueError("Window duration t_b - t_a must be positive")
    in_window = [(float(t), float(c)) for t, c in samples if float(t_a) <= float(t) <= float(t_b)]
    in_window.sort(key=lambda item: item[0])
    if len(in_window) < 2:
        return 0.0
    total_delta = 0.0
    for idx in range(1, len(in_window)):
        total_delta += counter_delta(in_window[idx - 1][1], in_window[idx][1])
    return total_delta / dt


def is_stale(t_sample: float, t_last: Optional[float], lookback: float = DEFAULT_LOOKBACK_SEC) -> bool:
    """True when t_sample - t_last > lookback (or t_last is None)."""
    if t_last is None:
        return True
    return (float(t_sample) - float(t_last)) > float(lookback)


def eval_with_lookback(
    value: Optional[float],
    t_sample: float,
    t_last: Optional[float],
    lookback: float = DEFAULT_LOOKBACK_SEC,
) -> float:
    """Return float(value) if reachable within lookback, else float('nan') (StaleNaN)."""
    if value is None or is_stale(t_sample, t_last, lookback):
        return float("nan")
    return float(value)


def project_grafana_envelope(
    samples: Sequence[Tuple[float, Optional[float]]],
    t_start: float,
    t_end: float,
    width_px: int,
    height_px: int,
    lookback: float = DEFAULT_LOOKBACK_SEC,
) -> Dict[str, Any]:
    """Project samples onto W_px buckets with [min, max] envelope and StaleNaN gaps."""
    if t_end <= t_start:
        raise ValueError("t_end must be > t_start")
    if width_px <= 0 or height_px <= 0:
        raise ValueError("width_px and height_px must be positive")

    ordered = sorted(((float(t), v) for t, v in samples), key=lambda p: p[0])
    finite_vals = [
        float(v)
        for t, v in ordered
        if float(t_start) <= t <= float(t_end) and v is not None and math.isfinite(float(v))
    ]
    v_min = min(finite_vals) if finite_vals else 0.0
    v_max = max(finite_vals) if finite_vals else 1.0
    if v_max == v_min:
        v_max = v_min + 1.0

    def _u(t: float) -> float:
        return float(width_px) * (t - float(t_start)) / (float(t_end) - float(t_start))

    def _w(v: float) -> float:
        return float(height_px) * (1.0 - (v - v_min) / (v_max - v_min))

    bucket_span = (float(t_end) - float(t_start)) / float(width_px)
    buckets: List[Dict[str, Any]] = []
    last_valid_t: Optional[float] = None
    for r in range(width_px):
        b_start = float(t_start) + r * bucket_span
        b_end = b_start + bucket_span
        bucket_vals: List[float] = []
        for t, v in ordered:
            if b_start <= t <= b_end if r == width_px - 1 else b_start <= t < b_end:
                if v is not None and math.isfinite(float(v)):
                    last_valid_t = t
                    bucket_vals.append(float(v))
        if not bucket_vals or is_stale(b_end, last_valid_t, lookback):
            buckets.append(
                {
                    "bucket": r,
                    "u_px": _u(0.5 * (b_start + b_end)),
                    "min_v": None,
                    "max_v": None,
                    "w_min_px": None,
                    "w_max_px": None,
                    "stale": True,
                }
            )
        else:
            lo = min(bucket_vals)
            hi = max(bucket_vals)
            buckets.append(
                {
                    "bucket": r,
                    "u_px": _u(0.5 * (b_start + b_end)),
                    "min_v": lo,
                    "max_v": hi,
                    "w_min_px": _w(lo),
                    "w_max_px": _w(hi),
                    "stale": False,
                }
            )
    return {
        "v_min": v_min,
        "v_max": v_max,
        "width_px": width_px,
        "height_px": height_px,
        "connect_nulls": False,
        "buckets": buckets,
        "design": DESIGN_CREDIT,
    }


@dataclass
class _MetricSlot:
    name: str
    mtype: str  # "gauge" or "counter"
    help_text: str
    value: float = 0.0
    last_ts: Optional[float] = None


class TelemetryRegistry:
    """Registry holding tau_handover, batch_index, handover_active, entanglement,
    and cdp_batches_total (never sovereign_workload).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._slots: Dict[str, _MetricSlot] = {
            "tau_handover": _MetricSlot(
                "tau_handover", "gauge", "Measured CDP handover latency tau_handover(t)"
            ),
            "batch_index": _MetricSlot(
                "batch_index", "gauge", "SIMD data_miner batch index k(t)"
            ),
            "handover_active": _MetricSlot(
                "handover_active", "gauge", "Binary CDP session liveness sigma_session(t)"
            ),
            "entanglement": _MetricSlot(
                "entanglement", "gauge", "Entanglement metric bound to Panel 105", value=1.0
            ),
            "cdp_batches_total": _MetricSlot(
                "cdp_batches_total", "counter", "Monotonic total SIMD batches processed"
            ),
        }

    def metric_names(self) -> List[str]:
        with self._lock:
            return list(self._slots.keys())

    def set_gauge(self, name: str, value: float, timestamp: float) -> None:
        with self._lock:
            slot = self._slots[name]
            if slot.mtype != "gauge":
                raise TypeError(f"{name} is not a gauge")
            slot.value = float(value)
            slot.last_ts = float(timestamp)

    def inc_counter(self, name: str, amount: float = 1.0, timestamp: Optional[float] = None) -> float:
        if float(amount) < 0.0:
            raise ValueError("Counter increment must be >= 0")
        with self._lock:
            slot = self._slots[name]
            if slot.mtype != "counter":
                raise TypeError(f"{name} is not a counter")
            slot.value += float(amount)
            if timestamp is not None:
                slot.last_ts = float(timestamp)
            return slot.value

    def sample_metric(
        self,
        name: str,
        t_sample: float,
        lookback: float = DEFAULT_LOOKBACK_SEC,
    ) -> float:
        with self._lock:
            slot = self._slots[name]
            return eval_with_lookback(slot.value, t_sample, slot.last_ts, lookback)

    def render_prometheus_text(self) -> str:
        with self._lock:
            lines: List[str] = []
            for slot in self._slots.values():
                lines.append(f"# HELP {slot.name} {slot.help_text}")
                lines.append(f"# TYPE {slot.name} {slot.mtype}")
                lines.append(f"{slot.name} {slot.value}")
            return "\n".join(lines) + "\n"


TELEMETRY_REGISTRY = TelemetryRegistry()
