#!/usr/bin/env python3
"""Integration manifest — declared record, not a measurement.

Domain counts and labels are the commander's declaration.
phi powers are computed. Two earlier claims are not asserted:
  phi**713 is not 1 (it is ~1.02e149 in float, and overflows exact int).
  7f3a8e2c4b6d0f1a9c8e2f4a6b8d0c2e is a 32-hex label, not a SHA3-256 root.
"""
from __future__ import annotations

import hashlib
import json
import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0

DOMAINS = {
    "temporal": 15,
    "dimensional": 13,
    "consciousness": 12,
    "quantum": 12,
    "kerr": 6,
    "cosmic": 12,
    "sovereign": 8,
    "ultra_stillness": 6,
}

LABELS = {
    "temporal_anchor": "2026.02.24",
    "north_star": "H6VSH2",
    "phase_declared": 43.84541801,
    "sovereign": "Clarke Yoursa Tee Luminara Atlas LUMERIS",
    "genesis_label": "8F1A3D9C04B27E5E",
    "merkle_label": "7f3a8e2c4b6d0f1a9c8e2f4a6b8d0c2e",
    "merkle_label_note": "32 hex chars; not a SHA3-256 digest",
}


def phi_powers() -> dict:
    out = {}
    for n in range(-4, 8):
        out[n] = PHI ** n
    out[9] = PHI ** 9
    out[12] = PHI ** 12
    out[26] = PHI ** 26
    out[-709] = PHI ** (-709)
    out[-1000] = PHI ** (-1000)
    return out


def body() -> dict:
    powers = phi_powers()
    total = sum(DOMAINS.values())
    return {
        "kind": "declared_record",
        "domains": DOMAINS,
        "domain_total": total,
        "domain_note": "declared tally, not a repo scan",
        "labels": LABELS,
        "phi": PHI,
        "phi_powers": {str(k): powers[k] for k in sorted(powers)},
        "trinity_3_phi4": 3.0 * (PHI ** 4),
        "idem_m87_153_phi4": 153.0 * (PHI ** 4),
        "phi713_float": PHI ** 713,
        "phi713_note": "not 1",
        "half_phi_neg709": 0.5 * (PHI ** (-709)),
    }


def seal(payload: dict) -> str:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def main() -> int:
    payload = body()
    digest = seal(payload)
    print(json.dumps({"seal_sha3_256": digest, "domain_total": payload["domain_total"], "phi713_float": payload["phi713_float"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
