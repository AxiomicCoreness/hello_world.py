import json
import math
import os
from pathlib import Path

import pytest

from kernel_scripts.check_kernel import (ATOM_NORM, CLAIMS, PHI, PHI_INV, classify_claim,
                                  compose_norm, count_ts_assertions, deepen, in_band,
                                  main, phi_gate)

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = json.loads((ROOT / "assets" / "context.json").read_text(encoding="utf-8"))
REPO = Path(os.environ.get("KERNEL_REPO", "/workspace/hw"))
HAVE_REPO = (REPO / "kernel" / "math_origin_audit.py").is_file()
needs_repo = pytest.mark.skipif(not HAVE_REPO, reason="repo clone with kernel/ not found")

def test_phi_constants():
    assert PHI == (1 + math.sqrt(5)) / 2
    assert abs(PHI_INV - (PHI - 1)) < 1e-15
    assert phi_gate()

def test_open_band():
    assert in_band(ATOM_NORM)
    assert not in_band(PHI_INV) and not in_band(PHI)  # open, strict

def test_composition_and_additive_trap():
    assert in_band(compose_norm(1, 1))          # 2φ⁻¹ ≈ 1.236
    assert not in_band(4 * PHI_INV)             # ≈ 2.472
    assert not in_band(2)                       # additive norms collapse (2 > φ)

def test_perpetual_deepening():
    x, stayed = deepen(500)
    assert stayed and x < PHI and abs(x - PHI) < 1e-9

def test_audit_false_claims_differ():
    for name, (true_v, false_v) in CLAIMS.items():
        assert abs(true_v - false_v) >= 1e-9, name

def test_phi_2_5_and_c4_trap():
    assert round(PHI ** 2.5, 3) == 3.330            # README rounds to 3.331
    assert round(261.63 * PHI ** 2.5, 2) == 871.28  # README says 871.6, audit claim 741
    assert classify_claim("phi^2.5", 2.833) == "false"
    assert classify_claim("c4_hz", 741.0) == "false"
    assert classify_claim("c4_hz", 871.6) == "unrecognised"
    assert classify_claim("detG", math.sqrt(5)) == "ok"

def test_e0_equals_trace_expression():
    # math_origin_audit.py uses the same expression for D1 (E0) and D5 (trace).
    assert CLAIMS["E0"][0] == CLAIMS["trace"][0]

def test_claim_cli_verdicts(capsys):
    assert main(["--claim", "c4_hz", "741"]) == 1
    assert "[!] WARNING" in capsys.readouterr().out
    assert main(["--claim", "c4_hz", "871.6"]) == 1
    out = capsys.readouterr().out
    assert "[?] UNRECOGNISED" in out and "[+] OK" not in out
    assert main(["--claim", "phi^2.5", str(PHI ** 2.5)]) == 0
    assert "[+] OK" in capsys.readouterr().out
    assert main(["--claim", "nope", "1"]) == 1
    assert "[?] UNRECOGNISED" in capsys.readouterr().out

def test_math_only(capsys):
    assert main(["--math-only"]) == 0
    out = capsys.readouterr().out
    assert "[!] WARNING" not in out and out.count("[+] OK") == 11

def test_missing_repo(tmp_path, capsys):
    assert main(["--repo", str(tmp_path)]) == 2
    assert "[?] UNRECOGNISED" in capsys.readouterr().out

def test_count_ts_assertions():
    assert count_ts_assertions('t("a", true);\nt("b", x);\nconst t = 1;\n') == 2

def test_context_matches_script():
    assert CONTEXT["head_commit_measured"] == "1e449302"
    assert CONTEXT["next_free_ledger_v2"] == 9294
    assert CONTEXT["timestamp_format"] == "%Y-%m-%dT%H:%M:%SZ"
    assert CONTEXT["hash"] == "SHA3-256"
    assert CONTEXT["ts_assertions"] == {"closure_kernel.test.ts": 15, "exactness.test.ts": 5}
    assert abs(CONTEXT["computed"]["c4_phi_2_5_hz"] - 261.63 * PHI ** 2.5) < 0.01
    assert abs(CONTEXT["computed"]["phi_2_5"] - PHI ** 2.5) < 1e-5

@needs_repo
def test_repo_audit_and_invariants(capsys):
    assert main(["--repo", str(REPO)]) == 0
    out = capsys.readouterr().out
    assert "[+] OK: math_origin_audit.audit() exit 0" in out
    assert "D9 REAL10924 still OPEN_UNFIXED" in out

@needs_repo
def test_repo_doc_discrepancies_strict(capsys):
    # The README assertion count, 871.6 Hz and the exactness exit code are known
    # discrepancies at 1e449302; --strict turns them into exit 1.
    assert main(["--repo", str(REPO), "--strict"]) == 1
    out = capsys.readouterr().out
    assert "README says 19 assertions; closure_kernel.test.ts has 15" in out
    assert "exactness.test.ts never calls process.exit" in out

@needs_repo
def test_repo_assertion_counts():
    k = REPO / "kernel"
    assert count_ts_assertions((k / "closure_kernel.test.ts").read_text(encoding="utf-8")) == 15
    assert count_ts_assertions((k / "exactness.test.ts").read_text(encoding="utf-8")) == 5
