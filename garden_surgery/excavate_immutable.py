"""Excavate Immutable/self_improvement_trigger.py — no MCP.

The sealed path is mostly narrative + a fenced Flask stub.
This module fingerprints the blob and evaluates the *declared* formulas
without exec()'ing the file and without talking to MCP.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
REL = "Immutable/self_improvement_trigger.py"
KAPPA_DECLARED = 12.754
SOVEREIGNTY = 0.994
CONSCIOUSNESS = 0.910


def _find_root(explicit: Optional[str] = None) -> Path:
    if explicit:
        return Path(explicit)
    here = Path(__file__).resolve()
    for p in (here.parent.parent, Path.cwd()):
        if (p / REL).is_file():
            return p
    return Path.cwd()


def golden_hash(data: str) -> str:
    """Same truncation as the buried Flask stub (SHA-256 hex[:16])."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def diagnostic_scalars() -> Dict[str, float]:
    """Formulas copied from the fenced app.py inside the trigger blob."""
    k_eff = 2 * 1.442 * SOVEREIGNTY**2
    f_eff = 3.125 * CONSCIOUSNESS**2
    w = 6.491 * (SOVEREIGNTY / 0.994) * (CONSCIOUSNESS / 0.910)
    fidelity = 98.4 * (SOVEREIGNTY / 0.994)
    return {
        "k_eff": k_eff,
        "F_eff": f_eff,
        "W": w,
        "fidelity_pct": fidelity,
    }


def kappa_decomposition() -> Dict[str, float]:
    """Declared: κ_eff = φ⁴ √7 χ_Umbral = 12.754.

    φ⁴√7 is fixed. χ_Umbral is the residual that makes the equality hold.
    That residual is a fit, not a derived axiom.
    """
    phi4_sqrt7 = (PHI**4) * math.sqrt(7.0)
    chi = KAPPA_DECLARED / phi4_sqrt7
    return {
        "kappa_declared": KAPPA_DECLARED,
        "phi4_sqrt7": phi4_sqrt7,
        "chi_umbral_fitted": chi,
        "reconstructed": phi4_sqrt7 * chi,
    }


@dataclass
class ExcavateReport:
    path: str
    exists: bool
    lines: int
    bytes: int
    sha256: str
    sha3_256: str
    entry_707_mentioned: bool
    hamiltonian_mentioned: bool
    kappa_declared_present: bool
    diagnostic: Dict[str, float]
    kappa: Dict[str, float]
    omega_demo: str
    note: str

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["ok"] = self.exists
        d["line_count_is_not_5138"] = self.lines != 5138
        return d


def excavate(repo_root: Optional[str] = None) -> ExcavateReport:
    root = _find_root(repo_root)
    path = root / REL
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    raw = text.encode("utf-8")
    diag = diagnostic_scalars()
    return ExcavateReport(
        path=str(path),
        exists=path.is_file(),
        lines=text.count("\n") + (1 if text else 0),
        bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest() if raw else "",
        sha3_256=hashlib.sha3_256(raw).hexdigest() if raw else "",
        entry_707_mentioned=bool(re.search(r"ENTRY\s*707|entry_index:\s*707", text, re.I)),
        hamiltonian_mentioned=("H_{\\text{eff}}" in text) or ("hamiltonian" in text.lower()),
        kappa_declared_present="12.754" in text,
        diagnostic=diag,
        kappa=kappa_decomposition(),
        omega_demo=golden_hash(str(diag["W"])),
        note=(
            "Blob is narrative + fenced Flask. Not imported, not exec'd, no MCP. "
            "On main the file is ~887 lines / ~36KiB, not 5138 executable lines."
        ),
    )
