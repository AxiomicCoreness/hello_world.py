import json
import math
from pathlib import Path

from scripts.recalc_optics import (NORTH_STAR_HZ, PHASE_LOCK_DEG, calc_lambda0,
                                   check_north_star, classify_lambda0, main)

CONTEXT = json.loads((Path(__file__).resolve().parents[1] / "assets" / "context.json")
                     .read_text(encoding="utf-8"))

def test_canonical_lambda0():
    lam = calc_lambda0(535805.0, 202.60)
    assert round(lam, 1) == 952072.1

def test_phi_pi_trap():
    # The drift report proves phi*pi/2 is NOT 202.6 degrees.
    phi = (1 + math.sqrt(5)) / 2
    phi_pi_2_deg = math.degrees(phi * math.pi / 2)
    assert round(phi_pi_2_deg, 2) == 145.62
    assert round(phi_pi_2_deg, 1) != 202.6

def test_consistency_951145():
    # The alternative design branch
    lam = 951145.0
    sum_theta = 360.0 * 535805.0 / lam
    assert round(sum_theta, 3) == 202.797

def test_deprecated_draft_sum_theta():
    # The deprecated draft gives 202.603 deg, not 202.610 deg.
    sum_theta = 360.0 * 535805.0 / 952057.0
    assert round(sum_theta, 3) == 202.603

def test_classify_lambda0_verdicts():
    assert classify_lambda0(952072.06) == "canonical"
    assert classify_lambda0(952057.0) == "deprecated"
    assert classify_lambda0(951145.0) == "unrecognised"

def test_unrecognised_prints_verdict(capsys):
    assert main(["--nkt-sum", "535805", "--theta-lock", "202.797"]) == 0
    out = capsys.readouterr().out
    assert "[?] UNRECOGNISED" in out
    assert "[+] OK" not in out and "[!] WARNING" not in out

def test_north_star_constant_matches_context():
    assert NORTH_STAR_HZ == 71.975
    assert CONTEXT["north_star_hz"] == NORTH_STAR_HZ
    assert CONTEXT["phase_lock_degrees"] == PHASE_LOCK_DEG == CONTEXT["theta_lock_deg"]

def test_north_star_flag(capsys):
    assert check_north_star(71.975)
    assert not check_north_star(71.9752029349341)  # phi^5 * 6.49, an approximation
    assert main(["--north-star"]) == 0
    assert "[+] North Star: 71.975 Hz" in capsys.readouterr().out
    assert main(["--north-star", "72"]) == 1
    assert "[!] North Star: 72 Hz != 71.975 Hz." in capsys.readouterr().out
