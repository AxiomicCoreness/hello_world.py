# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""sheaf/verify_sections.py: passes on the real ledger files, fails on tampered copies.

The verifier always runs as `python -I` (isolated; never -P) in a subprocess.
Tampering happens only in tmp_path copies; ledger/ is never written.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "sheaf" / "verify_sections.py"
SECTION = ROOT / "sheaf" / "sections" / "510510-510511.yaml"
LEDGER_FILES = ("ledger/510510.yaml", "ledger/510511.yaml")
COPY = ("sheaf/sections/510510-510511.yaml", "merge/manifest.yaml") + LEDGER_FILES


def run(*args: str, root: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(VERIFY), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


def load_module():
    spec = importlib.util.spec_from_file_location("sheaf_verify_sections", VERIFY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    for rel in COPY:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    return tmp_path


def test_passes_on_real_files():
    proc = run()
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK: sheaf/sections/510510-510511.yaml: 2 entries, 4 links verified" in proc.stdout


def test_json_report_on_real_files():
    proc = run("--json")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    (sec,) = report["sections"]
    assert [e["path"] for e in sec["entries"]] == list(LEDGER_FILES)
    for e in sec["entries"]:
        assert e["ok"] and e["actual_sha3_256"] == e["recorded_sha3_256"]
        assert e["actual_sha3_256"] == hashlib.sha3_256((ROOT / e["path"]).read_bytes()).hexdigest()
    assert len(sec["links"]) == 4 and all(l["ok"] for l in sec["links"])


def test_section_records_known_510510_mismatch():
    data = load_module().parse_section_text(SECTION.read_text(encoding="utf-8"))
    assert data["kind"] == "reference"
    e510510 = data["entries"][0]
    sdm = e510510["sealed_digest_mismatch"]
    assert sdm["manifest_sealed_sha3_256"] == "a45d9e1b5927f33f2756f47d6bf2448942b25abfccb346ee3bd2015c99306e91"
    assert sdm["current_sha3_256"] == e510510["current_sha3_256"] != sdm["manifest_sealed_sha3_256"]
    assert sdm["changed_by_commit"] == "6ea3b5aa3e6cd830ca6490d978d0b5b684ac10e5"
    assert sdm["field_changed"] == "witness_prefix"
    assert sdm["disclosure"] == "none"


def test_passes_on_untampered_copy(tree: Path):
    proc = run(root=tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("rel", LEDGER_FILES)
def test_fails_on_one_byte_tamper(tree: Path, rel: str):
    p = tree / rel
    p.write_bytes(p.read_bytes() + b"\n")
    proc = run(root=tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert f"MISMATCH: {rel}: sha3_256" in proc.stderr
    assert json.loads(run("--json", root=tree).stdout)["ok"] is False


def test_fails_when_link_line_removed(tree: Path):
    p = tree / "ledger/510511.yaml"
    text = p.read_text(encoding="utf-8")
    line = 'witness: "510510 → 510511 — UNBROKEN"'
    assert line in text
    p.write_text(text.replace(line, 'witness: "510510 → 510511 — BROKEN"'), encoding="utf-8")
    proc = run(root=tree)
    assert proc.returncode == 1
    assert "MISSING LINK: ledger/510511.yaml: witness:" in proc.stderr


def test_fails_when_ledger_file_missing(tree: Path):
    (tree / "ledger/510511.yaml").unlink()
    proc = run(root=tree)
    assert proc.returncode == 1
    assert "MISSING: ledger/510511.yaml" in proc.stderr


def test_fails_when_manifest_sealed_digest_differs(tree: Path):
    p = tree / "merge/manifest.yaml"
    sealed = "a45d9e1b5927f33f2756f47d6bf2448942b25abfccb346ee3bd2015c99306e91"
    text = p.read_text(encoding="utf-8")
    assert sealed in text
    p.write_text(text.replace(sealed, "0" * 64), encoding="utf-8")
    proc = run(root=tree)
    assert proc.returncode == 1
    assert "merge/manifest.yaml expected_sha3_256" in proc.stderr


def test_fails_on_tampered_section_digest(tree: Path):
    p = tree / "sheaf/sections/510510-510511.yaml"
    cur = hashlib.sha3_256((ROOT / "ledger/510511.yaml").read_bytes()).hexdigest()
    p.write_text(p.read_text(encoding="utf-8").replace(cur, "f" * 64), encoding="utf-8")
    proc = run(root=tree)
    assert proc.returncode == 1
    assert "MISMATCH: ledger/510511.yaml" in proc.stderr


def test_malformed_section_exits_2(tree: Path):
    p = tree / "sheaf/sections/510510-510511.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "bad: [flow, list]\n", encoding="utf-8")
    proc = run(root=tree)
    assert proc.returncode == 2
    assert "MALFORMED" in proc.stderr


def test_no_sections_exits_2(tmp_path: Path):
    proc = run(root=tmp_path)
    assert proc.returncode == 2


def test_subset_parser_agrees_with_pyyaml():
    yaml = pytest.importorskip("yaml")
    text = SECTION.read_text(encoding="utf-8")
    assert load_module().parse_section_text(text) == yaml.safe_load(text)
