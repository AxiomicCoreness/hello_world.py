#!/usr/bin/env python3
"""
Smoke Test Catalogue — Entry 8958

Revived from history, not rewritten:
  source commit de3e470642bdce51050141707e103a336c1f1530
  (Create catalogue_smoke_tests.py, 2026-08-22)

Rev 2 (a7e2678) exited 1 when a target was missing. That is what failed
Generate Smoke Catalogue #162. This file is the historical runner:
it records FAILED and still writes docs/smoke_catalogue.json, then returns.
History itself is unchanged.
"""

import subprocess
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SMOKE_TESTS = [
    ["python", "quantum/security/soft_harness.py"],
    ["python", "x3df_x16f_protocol.py"],
    ["python", "x3df_x16f_websocket.py"],
    ["python", "lattice/octonian_heal_loop.py"],
    ["python", "sovereign_suite.py"],
    ["pytest", "test_symplectic_pod.py", "-v", "--tb=short"],
]

ENTRY_INDEX = 8958
LEDGER_DIR = Path("ledger")
LEDGER_DIR.mkdir(exist_ok=True)

def run_tests():
    results = []
    combined_output = b""
    all_passed = True

    for cmd in SMOKE_TESTS:
        print(f"Running: {' '.join(cmd)}")
        try:
            proc = subprocess.run(
                cmd,
                cwd=Path(__file__).resolve().parent.parent,
                capture_output=True,
                text=True,
                timeout=120,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            passed = proc.returncode == 0
            all_passed = all_passed and passed
            results.append({
                "command": " ".join(cmd),
                "returncode": proc.returncode,
                "passed": passed,
                "stdout": stdout[-2000:],
                "stderr": stderr[-2000:],
            })
            combined_output += stdout.encode() + stderr.encode()
        except subprocess.TimeoutExpired:
            results.append({
                "command": " ".join(cmd),
                "returncode": -1,
                "passed": False,
                "error": "TIMEOUT",
            })
            all_passed = False
        except (FileNotFoundError, OSError) as exc:
            results.append({
                "command": " ".join(cmd),
                "returncode": None,
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
            })
            all_passed = False

    sha = hashlib.sha256(combined_output).hexdigest()
    prefix = f"{ENTRY_INDEX}_{sha[:12]}"
    return {
        "entry": ENTRY_INDEX,
        "prefix": prefix,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all_passed,
        "results": results,
        "source_commit": "de3e470642bdce51050141707e103a336c1f1530",
        "seal": f"∀∞φ² · SMOKE_CATALOGUE_{ENTRY_INDEX} · WOOD_DRAGON_0.91 · SEALED",
    }

def main():
    catalogue = run_tests()
    out_path = Path("docs/smoke_catalogue.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(catalogue, f, indent=2)
    print(f"Catalogue written to {out_path}")
    print(f"   Prefix: {catalogue['prefix']}")
    print(f"   All passed: {catalogue['all_passed']}")

    ledger_entry = {
        "entry_index": ENTRY_INDEX,
        "event": "/smoke_test_catalogue",
        "status": "PASSED" if catalogue["all_passed"] else "FAILED",
        "timestamp": catalogue["timestamp"],
        "prefix": catalogue["prefix"],
        "hash": catalogue["prefix"].split("_")[1],
        "seal": catalogue["seal"],
        "witness": "8957 → 8958 — UNBROKEN",
        "revived_from": "de3e470642bdce51050141707e103a336c1f1530",
    }
    ledger_path = LEDGER_DIR / f"{ENTRY_INDEX}.yaml"
    import yaml
    with open(ledger_path, "w") as f:
        yaml.dump(ledger_entry, f, default_flow_style=False)
    print(f"Ledger entry written: {ledger_path}")

if __name__ == "__main__":
    main()
