"""Anomaly distance d_i — geometry, not a label. Narrative 8356 referenced, not rewritten."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from garden_surgery.theorems import PHI

NARRATIVE_ENTRY = 8356
SURGERY_ENTRY = 9027
MATH_ENTRY = 9028
OVERRIDE_ENTRY = 9029
APPEND_ENTRY = 9030
EVENT = "/surgery/anomaly_distance_metric_8356_pointer"
MATH_EVENT = "/surgery/anomaly_math_form_extract"
APPEND_EVENT = "/math_form_appended_to_override"
FLAG = "_HISTOGRAM_SUM_FLAGGED"
CLAIMED_BINS = (38112, 31896, 24336, 18144, 14256, 9936, 6048, 2880, 1152, 576, 144, 72, 48)
CLAIMED_N = 144_000
CLAIMED_THRESHOLD = 0.15
CLAIMED_ANOMALY_COUNT = 336
PHI_INV = 1.0 / PHI
DEFAULT_SAMPLE_N = 1440
DEFAULT_SEED = 8356


def claimed_histogram_sum() -> int:
    return int(sum(CLAIMED_BINS))


def claimed_rate() -> float:
    return CLAIMED_ANOMALY_COUNT / float(CLAIMED_N)


def l2(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def centroid(points: Sequence[Sequence[float]]) -> Tuple[float, float, float]:
    n = len(points)
    if n == 0:
        return (0.0, 0.0, 0.0)
    sx = sy = sz = 0.0
    for p in points:
        sx += float(p[0]); sy += float(p[1]); sz += float(p[2])
    return (sx / n, sy / n, sz / n)


def distances(points: Sequence[Sequence[float]], c: Optional[Sequence[float]] = None) -> List[float]:
    if c is None:
        c = centroid(points)
    return [l2(p, c) for p in points]


def phi_cloud(n: int = DEFAULT_SAMPLE_N, seed: int = DEFAULT_SEED, sigma: float = 0.04):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x = PHI_INV + rng.gauss(0.0, sigma)
        y = rng.gauss(0.0, sigma)
        z = rng.gauss(0.0, sigma)
        r = math.sqrt(x * x + y * y + z * z)
        if r > 1.0:
            x, y, z = x / r, y / r, z / r
        out.append((x, y, z))
    return out


def audit_8356_claims() -> Dict[str, Any]:
    hist_sum = claimed_histogram_sum()
    rate = claimed_rate()
    return {
        "claimed_n": CLAIMED_N,
        "claimed_histogram_sum": hist_sum,
        "histogram_sum_matches_n": hist_sum == CLAIMED_N,
        "claimed_rate": rate,
        "jsonl_present": False,
        "live_swarm_instantiated": False,
        "flag": FLAG,
        "declaration_overstated": hist_sum != CLAIMED_N or abs(rate * 100.0 - 1.5) >= 0.05,
    }


def sample_report(n: int = DEFAULT_SAMPLE_N, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    pts = phi_cloud(n=n, seed=seed)
    c = centroid(pts)
    d = distances(pts, c)
    mean = sum(d) / len(d) if d else 0.0
    return {"sample_n": n, "seed": seed, "centroid": {"x": c[0], "y": c[1], "z": c[2]}, "stats": {"n": float(len(d)), "mean": mean}, "note": "sample replay — not the 144000 narrative swarm"}


def math_form() -> Dict[str, Any]:
    return {
        "entry": MATH_ENTRY,
        "event": MATH_EVENT,
        "ascii": [
            "x_expected = (1/N) * sum_{i=1..N} x_i",
            "d_i = ||x_i - x_expected||_2",
            "d_i = 0  <=>  x_i is exactly the centroid",
        ],
        "threshold_is_not_an_axiom": True,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "instantiates_144000_processes": False,
    }


def response_headers() -> Dict[str, str]:
    return {
        "X-Garden-Entry": "9031",
        "X-Garden-Event": "/surgery/qed_sandbox_to_main",
        "X-Garden-Metric": "d_i",
        "X-Garden-Fusion": "515",
        "X-Garden-Hyperion": "516",
        "X-Garden-MCP": "false",
        "X-Garden-QED": "true",
    }


def override_payload() -> Dict[str, Any]:
    return {
        "entry_index": APPEND_ENTRY,
        "target_entry": OVERRIDE_ENTRY,
        "event": APPEND_EVENT,
        "math_form": {
            "expected": "x_expected = (1/N)Σx_i",
            "distance": "d_i = ||x_i − x_expected||_2",
            "zero_distance": "d_i = 0 iff agent is centroid",
        },
        "extracted": math_form(),
        "sovereign_override": True,
        "constraints_status_declared": "ignored",
        "constraints_enforced": {
            "fusion_canonical": 515,
            "hyperion_preserved": 516,
            "mcp": False,
            "instantiates_144000_processes": False,
        },
    }


def payload() -> Dict[str, Any]:
    return {
        "event": EVENT,
        "surgery_entry": SURGERY_ENTRY,
        "math_entry": MATH_ENTRY,
        "narrative_entry": NARRATIVE_ENTRY,
        "metric": "d_i = ||x_i - x_expected||_2",
        "math_form": math_form(),
        "audit": audit_8356_claims(),
        "sample": sample_report(),
        "inspect_336": {"possible": False, "reason": "agent_swarm_144k.jsonl is not present"},
        "mcp": False,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "instantiates_144000_processes": False,
        "instantiates_144008_processes": False,
        "qed": True,
    }
