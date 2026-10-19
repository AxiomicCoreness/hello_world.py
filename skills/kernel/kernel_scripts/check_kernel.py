#!/usr/bin/env python3
"""Re-check the invariants of the repo's kernel/ directory (head 1e449302).

Verdicts: [+] OK, [!] WARNING, [?] UNRECOGNISED.
Exit: 0 all invariants hold; 1 an invariant failed (or a doc discrepancy under
--strict, or a --claim that is not OK); 2 repo kernel/ not found.
"""
import argparse
import contextlib
import importlib.util
import io
import math
import os
import re
import sys
from pathlib import Path

PHI = (1 + math.sqrt(5)) / 2          # closure_kernel.ts:13, math_origin_audit.py:26
PHI_INV = 1 / PHI                     # closure_kernel.ts:14
ATOM_NORM = 1                         # closure_kernel.ts:15
PHI_GATE_EPS = 1e-15                  # math_origin_audit.py:32
DEPTH = 500                           # closure_kernel.test.ts:16
LEX0_ATOMS = 13                       # closure_kernel.ts:44
C4_HZ = 261.63                        # math_origin_audit.py:78
REAL10924 = 10924                     # math_origin_audit.py:28
DEFAULT_REPO = os.environ.get("KERNEL_REPO", "/workspace/hw")

# Values recomputed exactly as math_origin_audit.py DEFECTS does (lines 60-78).
# (true value, false claim recorded in the audit)
CLAIMS = {
    "E0":        (1.0 - 2.0 / PHI + PHI ** 2, -3.236068),
    "detG":      (PHI ** 2 - PHI ** -2, -1.0),
    "HB":        (1 / PHI - 1.0, 1 / PHI),
    "frobenius": (math.sqrt(1.0 + 2.0 * (1 / PHI) ** 2 + (PHI ** 2) ** 2), 5.0),
    "trace":     (1.0 - 2.0 / PHI + PHI ** 2, 0.0),
    "phi^2.5":   (PHI ** 2.5, 2.833),
    "c4_hz":     (C4_HZ * PHI ** 2.5, 741.0),
}

def in_band(n: float) -> bool:
    """Open band phi^-1 < n < phi (closure_kernel.ts:16)."""
    return PHI_INV < n < PHI

def compose_norm(a: float, b: float) -> float:
    """(|w0| + |w1|) * phi^-1 (closure_kernel.ts:24)."""
    return (a + b) * PHI_INV

def phi_gate(eps: float = PHI_GATE_EPS) -> bool:
    """The three identities of math_origin_audit.phi_gate (lines 34-36)."""
    return (abs(PHI ** 2 - PHI - 1.0) <= eps
            and abs(1 / PHI - (PHI - 1.0)) <= eps
            and abs((1 / PHI) ** 2 - (2.0 - PHI)) <= eps)

def deepen(depth: int = DEPTH, x: float = ATOM_NORM):
    """Iterate x -> (x+1)/phi; return (final x, stayed in band)."""
    for _ in range(depth):
        x = compose_norm(x, ATOM_NORM)
        if not in_band(x):
            return x, False
    return x, True

def classify_claim(name: str, value: float, tol: float = 1e-6) -> str:
    """'ok' (matches recomputed value), 'false' (matches the audited false
    claim) or 'unrecognised' (neither, within tol)."""
    true_v, false_v = CLAIMS[name]
    if abs(value - true_v) <= tol:
        return "ok"
    if abs(value - false_v) <= tol:
        return "false"
    return "unrecognised"

def load_audit(kdir: Path):
    spec = importlib.util.spec_from_file_location("math_origin_audit", kdir / "math_origin_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def count_ts_assertions(text: str) -> int:
    return len(re.findall(r'^t\(', text, flags=re.M))

class Report:
    def __init__(self):
        self.failed = False
        self.doc_warn = False
    def ok(self, msg):
        print(f"[+] OK: {msg}")
    def warn(self, msg, doc=False):
        print(f"[!] WARNING: {'doc: ' if doc else ''}{msg}")
        if doc:
            self.doc_warn = True
        else:
            self.failed = True
    def check(self, cond, ok_msg, warn_msg, doc=False):
        self.ok(ok_msg) if cond else self.warn(warn_msg, doc)

def check_math(r: Report):
    r.check(phi_gate(), "φ gate: φ²=φ+1, 1/φ=φ−1, φ⁻²=2−φ (eps 1e-15)", "φ gate broken")
    r.check(in_band(ATOM_NORM) and not in_band(PHI_INV) and not in_band(PHI),
            "band is open: ‖t‖=1 inside, φ⁻¹ and φ excluded", "band/atom invariant broken")
    r.check(in_band(compose_norm(1, 1)) and not in_band(4 * PHI_INV) and not in_band(2),
            "pair 2φ⁻¹ in band; 4φ⁻¹ and additive 2 outside", "composition invariant broken")
    x, stayed = deepen()
    r.check(stayed and x < PHI and abs(x - PHI) < 1e-9,
            f"{DEPTH}-deep composition stays in band, x={x!r} < φ",
            f"deepening left the band or did not converge (x={x!r})")
    for name, (true_v, false_v) in CLAIMS.items():
        r.check(abs(true_v - false_v) >= 1e-9,
                f"{name}: recomputed {true_v:.6f} ≠ audited claim {false_v:g}",
                f"{name}: audited claim {false_v:g} now matches (stale entry)")

def check_repo(r: Report, repo: Path) -> int:
    kdir = repo / "kernel"
    if not (kdir / "math_origin_audit.py").is_file():
        print(f"[?] UNRECOGNISED: no kernel/math_origin_audit.py under {repo}")
        return 2
    mod = load_audit(kdir)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.audit()
    r.check(rc == 0, "math_origin_audit.audit() exit 0",
            f"math_origin_audit.audit() exit {rc}: {buf.getvalue().strip()}")
    r.check(abs(mod.PHI - PHI) == 0, "audit PHI equals (1+√5)/2", "audit PHI differs")
    st = {k: d["status"] for k, d in mod.DEFECTS.items()}
    fixed = sum(1 for s in st.values() if s == "FIXED_LANDED")
    r.check(len(st) == 11 and fixed == 8, "11 defects, 8 FIXED_LANDED",
            f"defect counts changed: {len(st)} total, {fixed} fixed")
    r.check(st.get("D9_REAL10924_signature_check") == "OPEN_UNFIXED"
            and mod.LAYER_MAP["special"].get("REAL10924") == REAL10924,
            "D9 REAL10924 still OPEN_UNFIXED (rename is not remediation)",
            "D9 status/binding changed; re-audit before citing")
    r.check(st.get("D6_frequency_box_741Hz") == "OPEN_DOCUMENTATION"
            and st.get("D11_hypersurface_pending_constants") == "OPEN_PENDING_MATH_ORIGIN",
            "D6 OPEN_DOCUMENTATION, D11 OPEN_PENDING_MATH_ORIGIN",
            "D6/D11 status changed")
    for name, key in (("E0", "D1_sovereign_hamiltonian_E0"), ("detG", "D2_sovereign_hamiltonian_detG"),
                      ("HB", "D3_sovereign_hamiltonian_HB"), ("frobenius", "D4_sovereign_hamiltonian_frobenius"),
                      ("trace", "D5_sovereign_hamiltonian_trace"), ("c4_hz", "D6_frequency_box_741Hz")):
        d = mod.DEFECTS[key]
        r.check(abs(d["actual_value"] - CLAIMS[name][0]) < 1e-12 and d["claimed_value"] == CLAIMS[name][1],
                f"{key} matches reimplementation", f"{key} differs from reimplementation")

    # documentation discrepancies (do not fail unless --strict)
    readme = (kdir / "README.md").read_text(encoding="utf-8")
    ck_test = (kdir / "closure_kernel.test.ts").read_text(encoding="utf-8")
    ex_test = (kdir / "exactness.test.ts").read_text(encoding="utf-8")
    n = count_ts_assertions(ck_test)
    m = re.search(r"\((\d+) assertions", readme)
    if m:
        r.check(int(m.group(1)) == n, f"README assertion count {n}",
                f"README says {m.group(1)} assertions; closure_kernel.test.ts has {n}", doc=True)
    hz = re.search(r"261\.63 Hz × φ\^2\.5 ≈ ([\d.]+) Hz", readme)
    if hz:
        doc = float(hz.group(1)); calc = C4_HZ * PHI ** 2.5
        r.check(abs(doc - calc) < 0.05, f"README C4·φ^2.5 ≈ {doc} Hz",
                f"README says {doc} Hz; 261.63·φ^2.5 = {calc:.2f} Hz", doc=True)
    p = re.search(r"φ\^2\.5 ≈ ([\d.]+) \(not", readme)
    if p:
        doc = float(p.group(1)); calc = PHI ** 2.5
        r.check(round(calc, len(p.group(1).split(".")[1])) == doc, f"README φ^2.5 ≈ {doc}",
                f"README says φ^2.5 ≈ {doc}; φ^2.5 = {calc:.5f}", doc=True)
    r.check("process.exit" in ex_test, "exactness.test.ts sets exit code",
            "exactness.test.ts never calls process.exit: FAIL lines still exit 0", doc=True)
    return 0

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Re-check kernel/ invariants (φ-band, audit ledger).")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="repo clone root (default %(default)s)")
    ap.add_argument("--math-only", action="store_true", help="skip repo file checks")
    ap.add_argument("--strict", action="store_true", help="doc discrepancies also exit 1")
    ap.add_argument("--claim", nargs=2, metavar=("NAME", "VALUE"),
                    help=f"classify a value; NAME in {', '.join(CLAIMS)}")
    ap.add_argument("--tol", type=float, default=1e-6, help="tolerance for --claim")
    a = ap.parse_args(argv)

    if a.claim:
        name, raw = a.claim
        if name not in CLAIMS:
            print(f"[?] UNRECOGNISED: claim name {name!r}; known: {', '.join(CLAIMS)}")
            return 1
        v = float(raw); true_v, false_v = CLAIMS[name]
        verdict = classify_claim(name, v, a.tol)
        if verdict == "ok":
            print(f"[+] OK: {name} = {v:g} matches recomputed {true_v:.6f}.")
            return 0
        if verdict == "false":
            print(f"[!] WARNING: {name} = {v:g} is the audited false claim; recomputed {true_v:.6f}.")
        else:
            print(f"[?] UNRECOGNISED: {name} = {v:g} matches neither recomputed {true_v:.6f} "
                  f"nor audited claim {false_v:g} (±{a.tol:g}).")
        return 1

    r = Report()
    check_math(r)
    if not a.math_only:
        rc = check_repo(r, Path(a.repo))
        if rc:
            return rc
    return 1 if r.failed or (a.strict and r.doc_warn) else 0

if __name__ == "__main__":
    sys.exit(main())
