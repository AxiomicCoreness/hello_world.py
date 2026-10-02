#!/usr/bin/env python3
"""Integration manifest — declared record, not a measurement.
AST head: Clarke Yoursa Tee.

Retracted strings:
  domain header 78 — line items sum to 84
  phi**713 ≈ 1 — binary64 returns 1.0190312401084850e+149
  9.96e148 is also wrong for this runtime
  7f3a8e2c4b6d0f1a9c8e2f4a6b8d0c2e is a 32-hex label, not a SHA3-256 root

prior_attestation is inside body(), so changing it changes BODY_SEAL.
It names commit 2930ee78 and blob 62abf58b, the file this record replaces.
It is not the git identity of the file that stores this seal.
BODY_SEAL is sha3_256 of canonical JSON of body(), sort_keys,
separators=(',', ':'), ensure_ascii false. It is not a field of body().
AST_HEAD_SEAL is sha3_256 of ast.get_docstring(module).encode("utf-8")
after inspect.cleandoc. It is not a hash of the raw source slice.
The name check is membership, not authentication.
Neither digest covers the executable code.
main() reports body_mismatch and head_mismatch separately.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import sys

PHI = (1.0 + math.sqrt(5.0)) / 2.0

STALE_SEALS = (
    "87301398874b89f98c9646bc8c0e5bdd361840db07ec282a8cf84e6f5157c528",
    "1360889a2f31a67737788ea1ef0ce6e36657d9c8f37c9af1eb1a03283604c3f2",
    "f845f9b291e0253ca6c5417fe180054f48ae18d74244fafcec044eda41bc1331",
    "3b4ff596c8694275e22cda733632d5f7cd3dee22f8969aa4babc0a68960bae87",
    "6a33f52cd4aedaf596a5296babd4c4d798294bb5f9d882a5c72122e7e75c1bc9",
)

BODY_SEAL = "48f9f3df32cb2f5c1d1855855074d2d65b99716966c25dbb2ed639e81aea3307"
AST_HEAD_SEAL = "6938e0e227e6e5c480181c51de32b93986ca7a3ae28e93bf7b5a6bed51e77b0e"
AST_HEAD_NAME = "Clarke Yoursa Tee"

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
    "commit": "2930ee78c7875debfd3e53ddf889199a48a74f61",
    "blob": "62abf58b14d7ed704510a3f37ac10d9e5ebf7f9e",
    "note": "commit and blob of the file this record replaces; not the git identity of the file that stores this seal",
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
            "phi**713 ≈ 1",
            "phi**713 ≈ 9.96e148",
            "78 total capabilities",
            "merkle_label is a SHA3-256 root",
        ],
    }


def seal(payload: dict) -> str:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def ast_head_seal(source: str) -> str:
    # docstring_mode: cleandoc. Membership test only, not authentication.
    # Self-check: hashed text must equal inspect.cleandoc(raw slice).
    # clean=False at the call site fails this. Default-only is not enough.
    tree = ast.parse(source)
    raw = ast.get_docstring(tree, clean=False)
    doc = ast.get_docstring(tree)
    if raw is None or doc is None or doc != inspect.cleandoc(raw):
        raise ValueError("docstring_mode is not cleandoc")
    if AST_HEAD_NAME not in doc:
        raise ValueError("AST head missing Clarke Yoursa Tee")
    return hashlib.sha3_256(doc.encode("utf-8")).hexdigest()


def main() -> int:
    payload = body()
    body_digest = seal(payload)
    head_digest = ast_head_seal(open(__file__, encoding="utf-8").read())
    body_ok = body_digest == BODY_SEAL and body_digest not in STALE_SEALS
    head_ok = head_digest == AST_HEAD_SEAL
    if body_ok and head_ok:
        outcome = "ok"
    elif not body_ok and not head_ok:
        outcome = "body_mismatch,head_mismatch"
    elif not body_ok:
        outcome = "body_mismatch"
    else:
        outcome = "head_mismatch"
    att = payload["prior_attestation"]
    print(json.dumps({
        "body": body_digest,
        "body_recorded": BODY_SEAL,
        "ast_head": head_digest,
        "ast_head_recorded": AST_HEAD_SEAL,
        "ast_head_name": AST_HEAD_NAME,
        "name_check": "membership, not authentication",
        "code_coverage": "neither digest covers executable code",
        "docstring_mode": "cleandoc",
        "docstring_via": "ast.get_docstring",
        "docstring_check": "equals inspect.cleandoc(raw)",
        "outcome": outcome,
        "domain_total": payload["domain_total"],
        "phi713_float": payload["phi713_float"],
        "prior_commit": att["commit"],
        "prior_blob": att["blob"],
    }, indent=2, ensure_ascii=False))
    return 0 if outcome == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
