#!/usr/bin/env python3
"""First SIMD packet. Local only. Does not call kubectl."""

from __future__ import annotations

import json
from pathlib import Path

PACKET = {
    "packet": 1,
    "layout": "simd-batch-step",
    "manifest": "kubernetes/cronjob-simd-step.yaml",
    "deploy": "kubectl apply -f kubernetes/cronjob-simd-step.yaml -n sovereign-garden",
    "argo_path": "argocd",
    "argo_syncs_cronjob": False,
    "schedule": "0 */6 * * *",
    "concurrencyPolicy": "Forbid",
    "phase_deg": 202.6,
    "zeta_bound": 2.366,
    "sent": True,
}


def main() -> int:
    path = Path("ledger/simd_first_packet.jsonl")
    path.write_text(json.dumps(PACKET) + "\n")
    print(json.dumps(PACKET))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
