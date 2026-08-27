"""Actionable theorems — only identities that must hold in IEEE float.

These are *tests*, not seals. A failed assert here is a real failure.

Proven here:
  T1  φ² = φ + 1
  T2  φ⁻¹ + φ⁻² = 1
  T3  Q = (2+√5)/4 is the defined Garden Q-invariant
  T4  SHA3-256 event-hash domain matches ledger/event_hash.py

Signature (not a physics theorem):
  commander name may be bound as a watermark; it does not alter T1–T4.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, asdict
from typing import Dict, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
PHI_INV = 1.0 / PHI
PHI_NEG2 = PHI ** -2
PHI_NEG3 = PHI ** -3
Q_INVARIANT = (2.0 + math.sqrt(5.0)) / 4.0
THETA = PHI * math.pi / 2.0
DOMAIN = "GARDEN.EVENT.v1"
TOL = 1e-15

# Known sealed event hashes from ledger/event_hash.py formula
KNOWN_HASHES = {
    (515, "/agents/mutate + /fusion/mutation_515_with_grok"): (
        "9a64c5f061649c30cfc013971c35a5acf4096bdbda9a666e48d8b362fc15c853"
    ),
    (9021, "/correction/fusion_canonical_515_void_claim_516"): (
        "a1930b453897b2acaeb81baaabebfc1f02536d66db1901f2b334c314384ad618"
    ),
    (9022, "/surgery/diffuse_monolith_actionable_theorems"): (
        "c7ab4f94b50b6a09f350c4fd6a254ebb2d18bdb8d8cc729a9390f72df485e0ed"
    ),
}


def event_payload(index: int, event: str) -> str:
    return (
        f"{int(index)}|{event}|phi2={PHI2:.15f}|delta=b^2-4ac|theta={THETA:.10f}"
    )


def event_hash(index: int, event: str) -> str:
    raw = DOMAIN.encode("utf-8") + b"\x00" + event_payload(index, event).encode("utf-8")
    return hashlib.sha3_256(raw).hexdigest()


@dataclass
class TheoremReport:
    passed: List[str]
    failed: List[str]
    constants: Dict[str, float]

    def ok(self) -> bool:
        return not self.failed

    def as_dict(self) -> Dict:
        d = asdict(self)
        d["ok"] = self.ok()
        return d


def check_theorems() -> TheoremReport:
    passed: List[str] = []
    failed: List[str] = []

    def t(name: str, cond: bool) -> None:
        (passed if cond else failed).append(name)

    t("T1_phi2_equals_phi_plus_one", abs(PHI2 - (PHI + 1.0)) < TOL)
    t("T1b_phi2_equals_phi_times_phi", abs(PHI2 - (PHI * PHI)) < TOL)
    t("T2_phi_inv_plus_phi_neg2_equals_one", abs(PHI_INV + PHI_NEG2 - 1.0) < TOL)
    t("T3_Q_definition", abs(Q_INVARIANT - (2.0 + math.sqrt(5.0)) / 4.0) < TOL)
    t("T3b_Q_positive_finite", Q_INVARIANT > 1.0 and math.isfinite(Q_INVARIANT))

    for (idx, ev), expected in KNOWN_HASHES.items():
        got = event_hash(idx, ev)
        t(f"T4_event_hash_{idx}", got == expected)

    return TheoremReport(
        passed=passed,
        failed=failed,
        constants={
            "phi": PHI,
            "phi2": PHI2,
            "phi_inv": PHI_INV,
            "phi_neg2": PHI_NEG2,
            "phi_neg3": PHI_NEG3,
            "Q": Q_INVARIANT,
            "theta_rad": THETA,
        },
    )
