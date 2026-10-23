"""Immunize: CORRECTED DM φ residual (ledger 8550 math_origin). Append-only; no seal rewrite."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI7 = PHI ** 7
DM = 1204.0
RESIDUAL = 41.46799191335416
SHA3_8550 = "be817a98c0ff2514a80e736d72df1a59d4ede4dc83fb5c82dfbcbea5a29346f1"


def test_reject_phi7_times_1000():
    wrong = PHI7 * 1000.0
    assert not math.isclose(wrong, DM, abs_tol=1.0)
    assert abs(wrong - 29034.441853748638) < 1e-6


def test_corrected_residual_exact():
    assert math.isclose(PHI7 * RESIDUAL, DM, abs_tol=1e-9)
    assert math.isclose(DM / PHI7, RESIDUAL, abs_tol=1e-12)


def test_nearest_phi15():
    assert math.isclose(PHI ** 15, 1364.0007331374366, abs_tol=1e-6)


def test_lattice_instance_corrected():
    inst = json.loads((ROOT / "frb_bridge_lattice_instance.json").read_text())
    frb = inst["frb"]
    assert frb["dm_pc_cm3"] == DM
    assert frb["phi_scaled_dm"] == DM
    assert frb.get("dm_check_ok") is True
    assert "41.46799191335416" in frb["dm_corrected_form"]
    assert abs(frb["dm_phi7_times_1000"] - 29034.441853748638) < 1e-6
    assert frb["dm_claim_prior_admissible"] is False
    assert frb["math_origin_sha3_8550"] == SHA3_8550


def test_generator_build_lattice_corrected():
    import importlib.util
    path = ROOT / "frb_bridge_generator.py"
    spec = importlib.util.spec_from_file_location("frb_bridge_generator", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lat = mod.build_lattice()
    frb = lat["frb"]
    assert frb["phi_scaled_dm"] == DM
    assert frb["dm_check_ok"] is True
    assert math.isclose(frb["dm_residual_factor"], RESIDUAL, abs_tol=1e-12)
    assert frb["math_origin_sha3_8550"] == SHA3_8550


def test_ledger_8550_math_origin_hash():
    text = (ROOT / "ledger" / "8550.yaml").read_text()
    assert SHA3_8550 in text
    assert "GARDEN.EVENT.v1" in text
    assert "dm_check_ok: true" in text
    assert "29034" in text  # rejected prior claim retained as witness
    assert "41.46799191335416" in text
