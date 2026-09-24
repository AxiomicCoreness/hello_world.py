#!/usr/bin/env python3
"""
Smoke Test Catalogue — Entry 8958 (rev 2, D17 remediation)

Rev 1 (53f9b08) recorded defects D17a-d. This revision remediates:
  D17a  ghost seal + asserted witness removed; replaced by a computed
        seal_sha3_256 digest over the canonical body (preimage-binding,
        same contract as verify_ledger_seals.py)
  D17b  sha256 -> sha3_256 (ledger/8767 policy); [:12] truncation removed;
        full 64-hex digest recorded
  D17c  output no longer truncated before hashing - the digest commits to
        the complete captured stdout+stderr
  D17d  missing/unlaunchable scripts no longer crash the run; they are
        recorded as failures (returncode None + error field) and the
        catalogue still gets written, with all_passed=False

Run status is whatever the tests actually produce. No PASSED claim is
made ahead of execution. No witness-chain claim is made: witness
continuity is verify_chain.py's job, not this script's.
"""

import subprocess
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

# List of smoke test commands (relative to repo root)
SMOKE_TESTS = [
    ["python", "quantum/security/soft_harness.py"],
    ["python", "x3df_x16f_protocol.py"],
    ["python", "x3df_x16f_websocket.py"],
    ["python", "lattice/octonian_heal_loop.py"],
    ["python", "sovereign_suite.py"],
]

ENTRY_INDEX = 8958
REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_DIR = REPO_ROOT / "ledger"
CATALOGUE_PATH = REPO_ROOT / "docs" / "smoke_catalogue.json"


def canonical(body: dict) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def run_tests() -> dict:
    results = []
    combined_output = b""
    all_passed = True

    for cmd in SMOKE_TESTS:
        print(f"Running: {' '.join(cmd)}")
        record = {"command": " ".join(cmd)}
        try:
            proc = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            record["returncode"] = proc.returncode
            record["passed"] = proc.returncode == 0
            record["stdout"] = proc.stdout
            record["stderr"] = proc.stderr
            combined_output += proc.stdout.encode() + proc.stderr.encode()
        except subprocess.TimeoutExpired:
            record["returncode"] = None
            record["passed"] = False
            record["error"] = "TIMEOUT"
        except (FileNotFoundError, OSError) as exc:
            # D17d: absent producer is a recorded failure, not a crash
            record["returncode"] = None
            record["passed"] = False
            record["error"] = f"{type(exc).__name__}: {exc}"
        all_passed = all_passed and record["passed"]
        results.append(record)

    # D17b/D17c: sha3_256 over the FULL combined output, no truncation
    output_sha3_256 = hashlib.sha3_256(combined_output).hexdigest()
    return {
        "entry": ENTRY_INDEX,
        "output_sha3_256": output_sha3_256,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all_passed,
        "results": results,
    }


def main() -> int:
    catalogue = run_tests()

    CATALOGUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOGUE_PATH.write_text(
        json.dumps(catalogue, indent=2), encoding="utf-8"
    )
    print(f"Catalogue written to {CATALOGUE_PATH}")
    print(f"  output_sha3_256: {catalogue['output_sha3_256']}")
    print(f"  all_passed: {catalogue['all_passed']}")

    # Ledger entry: seal_sha3_256 computed over the canonical body with
    # the seal field removed - the verify_ledger_seals.py contract.
    entry = {
        "entry_index": ENTRY_INDEX,
        "event": "/smoke_test_catalogue",
        "status": "PASSED" if catalogue["all_passed"] else "FAILED",
        "timestamp": catalogue["timestamp"],
        "output_sha3_256": catalogue["output_sha3_256"],
    }
    entry["seal_sha3_256"] = hashlib.sha3_256(
        canonical(entry).encode("utf-8")
    ).hexdigest()

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ledger_path = LEDGER_DIR / f"{ENTRY_INDEX}.yaml"
    ledger_path.write_text(
        yaml.safe_dump(entry, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Ledger entry written: {ledger_path}")
    print(f"  seal_sha3_256: {entry['seal_sha3_256']}")

    # A failed catalogue is a recorded FAILED status, not a suppressed one;
    # the exit code still reports the run verdict so CI can gate on it.
    return 0 if catalogue["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
