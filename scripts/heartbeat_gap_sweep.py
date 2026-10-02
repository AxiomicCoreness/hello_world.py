#!/usr/bin/env python3
"""6CAVD tensor heartbeat gap sweep. Sparse dict, lexicographic order, stdlib only."""
import itertools
from datetime import date

BRANCH = ["main"]
HEARTBEAT_CLASS = [
    "seal-verify",
    "rotate-keys",
    "mesh-pulse",
    "workflow-sync-6cavd",
    "other",
]
COMPLETION = ["completed", "incomplete"]  # gap is scan-derived, not written
CI_CLASS = ["ubuntu-latest", "self-hosted", "unknown"]
EVENT_KIND = ["live", "attest", "analysis", "ci_row_bookkeeping"]


def all_coords(days):
    return list(
        itertools.product(
            BRANCH,
            HEARTBEAT_CLASS,
            days,
            COMPLETION,
            CI_CLASS,
            EVENT_KIND,
        )
    )


def sweep(H: dict, days):
    expected = all_coords(days)
    gaps = [c for c in expected if c not in H]
    monotone = []
    prev = None
    ordered = [c for c in sorted(H) if H[c] > 0]
    for c in ordered:
        v = H[c]
        if prev is not None and v <= prev:
            monotone.append((c, v, prev))
        prev = v
    return gaps, monotone, expected


def main() -> int:
    days = [date(2026, 10, 1).isoformat()]
    H = {}
    H[
        (
            "main",
            "workflow-sync-6cavd",
            days[0],
            "completed",
            "ubuntu-latest",
            "ci_row_bookkeeping",
        )
    ] = 1
    H[
        (
            "main",
            "workflow-sync-6cavd",
            days[0],
            "incomplete",
            "ubuntu-latest",
            "ci_row_bookkeeping",
        )
    ] = 0

    gaps, monotone, expected = sweep(H, days)
    hcr_a = len(gaps) / len(expected) if expected else 0.0
    print(f"expected coords : {len(expected)}")
    print(f"observed        : {len(H)}")
    print(f"gaps            : {len(gaps)}  HCR_A = {hcr_a:.4f}")
    print(f"monotonic viol  : {len(monotone)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
