"""Evals for the xcode-planck-engine skill. Reads repo sources; no network.

Numeric anchors come from executing PlanckEngine.run() on the bae409d0 tree.
Paste values (T_H≈1.25e-19, etc.) are NOT used — see SKILL.md deltas.
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

from xcode_planck_scripts import check_xcode

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
SWIFT = REPO_ROOT / "sovereign" / "PlanckEngine.swift"
PYTHON = REPO_ROOT / "sovereign" / "planck_engine_v2.py"
REQ = REPO_ROOT / "requirements.txt"
CTX = SKILL_ROOT / "assets" / "context.json"

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Measured via PlanckEngine.run() — do not replace with paste.
MEASURED = {
    "hawkingTempK": 84057832.67649437,
    "sBellCorrected": 4.576491222541475,
    "dSdtOption1": -1596.9844718999245,
    "dSdtOption2": -986.9906831399547,
    "eps145": 1.36705719514418e-209,
    "zetaBound": 4.320767762363209,
}


def _run():
    spec = importlib.util.spec_from_file_location("planck_engine_v2", PYTHON)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PlanckEngine.run()


def test_swift_has_xcode_integration_notes():
    text = SWIFT.read_text(encoding="utf-8")
    assert "XCODE INTEGRATION NOTES" in text
    assert "iOS 16.0+" in text
    assert "Graphviz is NOT used here" in text
    assert "Stdlib stripping is handled by Xcode" in text


def test_swift_has_sync_with_gate_stub():
    text = SWIFT.read_text(encoding="utf-8")
    assert "syncWithGate" in text
    assert re.search(r"static\s+func\s+syncWithGate\s*\(\s*base:\s*URL\s*\)", text)


def test_no_graphviz_import_in_swift():
    text = SWIFT.read_text(encoding="utf-8")
    assert not re.search(r"(?m)^\s*import\s+Graphviz\b", text)
    for other in (
        REPO_ROOT / "AxiomicApp.swift",
        REPO_ROOT / "ContentView.swift",
        REPO_ROOT / "RenderClient.swift",
    ):
        if other.is_file():
            body = other.read_text(encoding="utf-8")
            assert not re.search(r"(?m)^\s*import\s+Graphviz\b", body)
            assert "import graphviz" not in body


def test_python_swift_phi_constants_agree():
    swift = SWIFT.read_text(encoding="utf-8")
    py = PYTHON.read_text(encoding="utf-8")
    assert "static var phi: Double = (1.0 + sqrt(5.0)) / 2.0" in swift
    assert "PHI = (1.0 + math.sqrt(5.0)) / 2.0" in py
    for s, p in (
        ("phi_5", "PHI_5"),
        ("phi_9", "PHI_9"),
        ("phi_inv_709", "PHI_INV_709"),
        ("phi_inv_1000", "PHI_INV_1000"),
    ):
        assert s in swift and p in py


def test_si_constants_present_both_sides():
    swift = SWIFT.read_text(encoding="utf-8")
    py = PYTHON.read_text(encoding="utf-8")
    for val in ("6.67430e-11", "299792458.0", "1.054571817e-34", "1.380649e-23", "1.989e30"):
        assert val in swift and val in py


def test_requirements_pin_python_plotting_only():
    req = REQ.read_text(encoding="utf-8")
    assert re.search(r"(?m)^graphviz\s*>=", req)
    assert re.search(r"(?m)^seaborn\s*>=", req)
    swift = SWIFT.read_text(encoding="utf-8")
    head, _, _ = swift.partition("NOTE ON GRAPHVIZ")
    assert "import graphviz" not in head.lower()
    assert not re.search(r"(?m)^\s*import\s+Graphviz\b", swift)


def test_run_matches_measured_not_paste():
    got = _run()
    # Paste T_H was 1.25e-19 — code yields ~8.41e7; reject paste.
    assert not math.isclose(got["hawkingTempK"], 1.25e-19, rel_tol=0.1, abs_tol=1e-30)
    for key, exp in MEASURED.items():
        assert key in got
        assert math.isclose(got[key], exp, rel_tol=1e-9, abs_tol=0.0), (key, got[key], exp)
    # Near-paste keys still within loose rounding of paste (except hawkingTempK)
    assert math.isclose(got["sBellCorrected"], 4.576, rel_tol=0, abs_tol=1e-3)
    assert math.isclose(got["dSdtOption1"], -1597.0, rel_tol=0, abs_tol=0.02)
    assert math.isclose(got["dSdtOption2"], -987.0, rel_tol=0, abs_tol=0.02)


def test_context_json_records_measured_and_deltas():
    ctx = json.loads(CTX.read_text(encoding="utf-8"))
    assert ctx["xcode"]["header_landed_on_main"] is True
    assert ctx["xcode"]["header_marker"] == "XCODE INTEGRATION NOTES"
    assert "syncWithGate" in ctx["port380"]["swift_stub"]
    for key, exp in MEASURED.items():
        assert math.isclose(ctx["run_measured"][key], exp, rel_tol=1e-9, abs_tol=0.0)
    assert ctx["run_paste_vs_measured"]["hawkingTempK"]["paste"] == 1.25e-19
    assert abs(ctx["run_paste_vs_measured"]["hawkingTempK"]["abs_delta"]) > 1e6


def test_check_xcode_cli_ok():
    r = subprocess.run(
        [sys.executable, "-P", str(SKILL_ROOT / "xcode_planck_scripts" / "check_xcode.py")],
        capture_output=True,
        text=True,
        cwd=str(SKILL_ROOT),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[+] OK" in r.stdout


def test_package_is_not_named_scripts():
    import xcode_planck_scripts

    assert Path(xcode_planck_scripts.__file__).parent == SKILL_ROOT / "xcode_planck_scripts"
    assert not (SKILL_ROOT / "scripts").exists()
