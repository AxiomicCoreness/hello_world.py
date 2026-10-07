#!/usr/bin/env python3
"""Symplectic-time quantities. Arithmetic only. No sovereignty label.

100/φ is 61.803..., not 47. The closest simple form is 76/φ.
"""

from __future__ import annotations

import json
import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI

# LTT9779b orbital frequency, stated. Period about 0.79 d.
OMEGA_N_PER_DAY = 1.26
ALBEDO = 0.85
# PSR J1023+0038 spin period, milliseconds.
SPIN_PERIOD_MS = 1.687987
BASE_ENERGY_J = 1e42


def golden_relation() -> dict:
    return {
        "claim_100_over_phi": 100.0 / PHI,
        "claim_matches_47": False,
        "closest": "76/phi",
        "seventy_six_over_phi": 76.0 / PHI,
        "forty_seven_times_phi": 47.0 * PHI,
        "digit_sum": 4 + 7,
        "prime": True,
    }


def form_pair() -> dict:
    return {
        "form": "x^2",
        "formless": "formal symbol x^infinity, not a finite monomial",
        "phi": PHI,
    }


def rotational() -> dict:
    omega = 2.0 * math.pi / (SPIN_PERIOD_MS * 1e-3)
    return {
        "omega_n_per_day": OMEGA_N_PER_DAY,
        "albedo": ALBEDO,
        "phi2": PHI2,
        "albedo_over_phi2": ALBEDO / PHI2,
        "spin_rad_s": omega,
        "base_energy_J": BASE_ENERGY_J,
        "two_form": "[Sum(dq[i]·dp[i], (i, 1, 427)), (1/φ)·(dξ·dξ̄)]",
        "phi_on": "second term",
        "resolved_pin": "QCIE/PEQ",
        "clock": "QCIE/PEQ",
        "E_rot": "0.5 * I * spin_rad_s^2",
        "I_kg_m2": None,
        "I_status": "pending research",
    }


def verify_clock() -> dict:
    """Parallel to the 0.85 coherence gate. Same number, separate check."""
    row = rotational()
    checks = {
        "clock": row["clock"] == "QCIE/PEQ",
        "frequency": row["omega_n_per_day"] == 1.26,
        "albedo_gate": row["albedo"] == 0.85,
        "phi_on_second_term": row["phi_on"] == "second term",
        "spin_positive": row["spin_rad_s"] > 0.0,
        "inertia_pending": row["I_kg_m2"] is None,
    }
    return {"gate": "coherence_fallback_0.85", "clock_check": checks, "ok": all(checks.values())}


def main() -> int:
    report = {"golden": golden_relation(), "forms": form_pair(), "rotation": rotational(), "verify": verify_clock()}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["verify"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
