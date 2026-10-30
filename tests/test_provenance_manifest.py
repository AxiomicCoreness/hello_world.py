# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Structure + runner checks for the provenance watermark campaign.

Does NOT require every file hash to match HEAD of an evolving main — the
manifest is a snapshot and goes stale as the tree moves. See the docstring
on scripts/verify_provenance_manifest.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PROVENANCE_MANIFEST.json"
SIDECAR = ROOT / "PROVENANCE_MANIFEST.sha256"
VERIFY = ROOT / "scripts" / "verify_provenance_manifest.py"


def test_manifest_present_and_shaped():
    assert MANIFEST.is_file(), "PROVENANCE_MANIFEST.json missing"
    assert SIDECAR.is_file(), "PROVENANCE_MANIFEST.sha256 missing"
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for key in ("repo", "base_commit", "author", "generated_at", "files"):
        assert key in data, f"missing {key}"
    assert isinstance(data["files"], list) and data["files"], "files empty"
    assert len(data["base_commit"]) == 40
    assert all(c in "0123456789abcdef" for c in data["base_commit"])
    sample = data["files"][0]
    assert "path" in sample and "sha256" in sample
    assert len(sample["sha256"]) == 64
    sidecar = SIDECAR.read_text(encoding="utf-8").strip().split()[0]
    assert len(sidecar) == 64


def test_verify_script_runs_with_isolated_python():
    assert VERIFY.is_file()
    # python -I: CI is 3.10; never use -P
    proc = subprocess.run(
        [sys.executable, "-I", str(VERIFY), "--root", str(ROOT)],
        capture_output=True,
        text=True,
    )
    # Fresh commit: should be OK (0). If someone edited after snapshot, still
    # assert the script produced a clear report and a known exit code.
    assert proc.returncode in (0, 1), (
        f"unexpected exit {proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    if proc.returncode == 0:
        assert "OK:" in proc.stdout
    else:
        joined = proc.stdout + proc.stderr
        assert any(
            tok in joined
            for tok in ("MISMATCH", "MISSING", "FAIL:", "MALFORMED", "SIDECAR")
        ), joined
