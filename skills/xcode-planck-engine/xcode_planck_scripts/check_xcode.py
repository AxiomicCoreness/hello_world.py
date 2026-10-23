#!/usr/bin/env python3
"""Validate Sovereign PlanckEngine Xcode wiring constraints.

Checks:
- sovereign/PlanckEngine.swift contains XCODE INTEGRATION NOTES and syncWithGate
- no Graphviz import in Swift sources
- φ definition agrees between Swift and sovereign/planck_engine_v2.py
- AxiomicApp.swift and ContentView.swift exist at repo root
- requirements.txt pins graphviz and seaborn (Python side only)
- PlanckEngine.run() anchors match measured values (not paste)

Exit 0 ok, 1 on failure. Prints [+] / [!] lines.
"""
from __future__ import annotations

import importlib.util
import math
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
SWIFT = REPO_ROOT / "sovereign" / "PlanckEngine.swift"
PYTHON = REPO_ROOT / "sovereign" / "planck_engine_v2.py"
REQ = REPO_ROOT / "requirements.txt"
APP = REPO_ROOT / "AxiomicApp.swift"
VIEW = REPO_ROOT / "ContentView.swift"

# Measured on bae409d0 tree via PlanckEngine.run() — NOT the paste.
MEASURED = {
    "hawkingTempK": 84057832.67649437,
    "sBellCorrected": 4.576491222541475,
    "dSdtOption1": -1596.9844718999245,
    "dSdtOption2": -986.9906831399547,
    "eps145": 1.36705719514418e-209,
    "zetaBound": 4.320767762363209,
}
REL_TOL = {
    "hawkingTempK": 1e-9,
    "sBellCorrected": 1e-12,
    "dSdtOption1": 1e-12,
    "dSdtOption2": 1e-12,
    "eps145": 1e-9,
    "zetaBound": 1e-12,
}


def _load_engine():
    spec = importlib.util.spec_from_file_location("planck_engine_v2", PYTHON)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PlanckEngine


def _errs() -> list[str]:
    errs: list[str] = []
    if not SWIFT.is_file():
        return [f"missing {SWIFT.relative_to(REPO_ROOT)}"]
    swift = SWIFT.read_text(encoding="utf-8")
    if "XCODE INTEGRATION NOTES" not in swift:
        errs.append("Swift missing XCODE INTEGRATION NOTES header")
    if "iOS 16" not in swift:
        errs.append("Swift header missing iOS 16.0+ target note")
    if "syncWithGate" not in swift:
        errs.append("Swift missing syncWithGate stub")
    if re.search(r"(?m)^\s*import\s+Graphviz\b", swift) or "import graphviz" in swift.lower():
        errs.append("Swift must not import Graphviz/graphviz")
    if not PYTHON.is_file():
        errs.append(f"missing {PYTHON.relative_to(REPO_ROOT)}")
    else:
        py = PYTHON.read_text(encoding="utf-8")
        if "PHI = (1.0 + math.sqrt(5.0)) / 2.0" not in py:
            errs.append("Python twin missing φ = (1+sqrt(5))/2 definition")
        if "static var phi: Double = (1.0 + sqrt(5.0)) / 2.0" not in swift:
            errs.append("Swift missing φ = (1+sqrt(5))/2 definition")
        for token in ("phi_5", "phi_9", "phi_inv_709", "phi_inv_1000"):
            if token not in swift:
                errs.append(f"Swift missing {token}")
        for token in ("PHI_5", "PHI_9", "PHI_INV_709", "PHI_INV_1000"):
            if token not in py:
                errs.append(f"Python missing {token}")
        try:
            engine = _load_engine()
            got = engine.run()
            for key, exp in MEASURED.items():
                if key not in got:
                    errs.append(f"run() missing key {key}")
                    continue
                tol = REL_TOL[key]
                if not math.isclose(got[key], exp, rel_tol=tol, abs_tol=0.0):
                    errs.append(f"run()[{key}]={got[key]!r} != measured {exp!r}")
        except Exception as e:
            errs.append(f"PlanckEngine.run() failed: {e}")
    for p in (APP, VIEW):
        if not p.is_file():
            errs.append(f"missing {p.name} at repo root")
    if REQ.is_file():
        req = REQ.read_text(encoding="utf-8")
        if "graphviz" not in req:
            errs.append("requirements.txt missing graphviz (Python plotting)")
        if "seaborn" not in req:
            errs.append("requirements.txt missing seaborn (Python plotting)")
    else:
        errs.append("missing requirements.txt")
    return errs


def main(argv: list[str] | None = None) -> int:
    errs = _errs()
    if errs:
        for e in errs:
            print(f"[!] {e}")
        print("[!] INVALID")
        return 1
    print("[+] XCODE INTEGRATION NOTES present")
    print("[+] syncWithGate stub present")
    print("[+] Swift/Python φ powers present")
    print("[+] no Graphviz import in Swift")
    print("[+] graphviz/seaborn pinned for Python")
    print("[+] PlanckEngine.run() matches measured anchors")
    print("[+] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
