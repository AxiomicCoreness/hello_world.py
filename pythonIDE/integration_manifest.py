#!/usr/bin/env python3
"""Integration manifest — declared record, not a measurement.

Retracted strings:
  domain header 78 — line items sum to 84
  phi**713 ≈ 1 — binary64 returns 1.0190312401084850e+149
  9.96e148 is also wrong for this runtime
  7f3a8e2c4b6d0f1a9c8e2f4a6b8d0c2e is a 32-hex label, not a SHA3-256 root

prior_attestation is inside body(), so changing it changes BODY_SEAL.
It names the previous file. It is not the git identity of this file.
BODY_SEAL is sha3_256 of canonical JSON of body(), sort_keys,
separators=(',', ':'). It is not a field of body().
main() recomputes it and exits 1 on mismatch.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys

PHI = (1.0 + math.sqrt(5.0)) / 2.0

STALE_SEALS = (
    "87301398874b89f98c9646bc8c0e5bdd361840db07ec282a8cf84e6f5157c528",
    "1360889a2f31a67737788ea1ef0ce6e36657d9c8f37c9af1eb1a03283604c3f2",
    "f845f9b291e0253ca6c5417fe180054f48ae18d74244fafcec044eda41bc1331",
)

BODY_SEAL = "3b4ff596c8694275e22cda733632d5f7cd3dee22f8969aa4babc0a68960bae87"

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

PRIOR_ATTESTATION = {
    "commit": "b4d42a1c6ad4b9abc23b4cc06fba1384184bfd15",
    "blob": "3e3dd8018c8721dbf4729579d2be083f3a754c55",
    "note": "identifies the previous file; not the git identity of the file that stores this seal",
}


def phi_powers() -> dict:
    out = {n: PHI ** n for n in range(-4, 8)}
    out[9] = PHI ** 9
    out[12] = PHI ** 12
    out[26] = PHI ** 26
    out[-709] = PHI ** (-709)
    out[-1000] = PHI ** (-1000)
    return out


def body() -> dict:
    powers = phi_powers()
    return {
        "kind": "declared_record",
        "domains": DOMAINS,
        "domain_total": sum(DOMAINS.values()),
        "domain_note": "declared tally, not a repo scan",
        "labels": LABELS,
        "prior_attestation": PRIOR_ATTESTATION,
        "phi": PHI,
        "phi_powers": {str(k): powers[k] for k in sorted(powers)},
        "trinity_3_phi4": 3.0 * (PHI ** 4),
        "idem_m87_153_phi4": 153.0 * (PHI ** 4),
        "phi713_float": PHI ** 713,
        "phi713_note": "binary64 1.0190312401084850e+149; not 1; not 9.96e148",
        "half_phi_neg709": 0.5 * (PHI ** (-709)),
        "retracted_strings": [
            "phi**713 \u2248 1",
            "phi**713 \u2248 9.96e148",
            "78 total capabilities",
            "merkle_label is a SHA3-256 root",
        ],
    }


def seal(payload: dict) -> str:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def main() -> int:
    payload = body()
    digest = seal(payload)
    ok = digest == BODY_SEAL and digest not in STALE_SEALS
    print(json.dumps({
        "seal_sha3_256": digest,
        "body_seal_recorded": BODY_SEAL,
        "match": ok,
        "domain_total": payload["domain_total"],
        "phi713_float": payload["phi713_float"],
        "phi_neg1000": payload["phi_powers"]["-1000"],
        "prior_attestation": payload["prior_attestation"],
        "stale_rejected": list(STALE_SEALS),
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
