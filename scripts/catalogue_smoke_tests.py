#!/usr/bin/env python3
"""
Smoke Test Catalogue — Entry 8958

Runner revived from de3e470642bdce51050141707e103a336c1f1530.
seal_sha3_256 backfill from a7e2678: digest is sha3-256 over the
canonical body with the seal_sha3_256 field excluded.
Missing targets are recorded. The catalogue is still written.
Exit 0 so the workflow can version; status carries PASSED or FAILED.
"""

import subprocess
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

SMOKE_TESTS = [
    ["python", "quantum/security/soft_harness.py"],
    ["python", "x3df_x16f_protocol.py"],
    ["python", "x3df_x16f_websocket.py"],
    ["python", "lattice/octonian_heal_loop.py"],
    ["python", "sovereign_suite.py"],
    ["pytest", "test_symplectic_pod.py", "-v", "--tb=short"],
]

ENTRY_INDEX = 8958
REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_DIR = REPO_ROOT / "ledger"
CATALOGUE_PATH = REPO_ROOT / "docs" / "smoke_catalogue.json"


def canonical(body: dict) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


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
                timeout=120,
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
            record["returncode"] = None
            record["passed"] = False
            record["error"] = f"{type(exc).__name__}: {exc}"
        all_passed = all_passed and record["passed"]
        results.append(record)

    return {
        "entry": ENTRY_INDEX,
        "output_sha3_256": hashlib.sha3_256(combined_output).hexdigest(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all_passed,
        "results": results,
        "revived_from": "de3e470642bdce51050141707e103a336c1f1530",
    }


def main() -> int:
    catalogue = run_tests()
    CATALOGUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOGUE_PATH.write_text(json.dumps(catalogue, indent=2), encoding="utf-8")
    print(f"Catalogue written to {CATALOGUE_PATH}")
    print(f"  output_sha3_256: {catalogue['output_sha3_256']}")
    print(f"  all_passed: {catalogue['all_passed']}")

    entry = {
        "entry_index": ENTRY_INDEX,
        "event": "/smoke_test_catalogue",
        "status": "PASSED" if catalogue["all_passed"] else "FAILED",
        "timestamp": catalogue["timestamp"],
        "output_sha3_256": catalogue["output_sha3_256"],
        "revived_from": catalogue["revived_from"],
        "hash_algo": "sha3_256",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
