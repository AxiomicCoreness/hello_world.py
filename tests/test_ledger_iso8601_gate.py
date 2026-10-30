# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""ledger_iso8601_gate: new entries need ISO 8601 with offset; legacy is report-only.

Each test builds a throwaway git repo in a temp dir with JSON-format entries,
so it runs under `python -I -m pytest` without PyYAML.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "ledger_iso8601_gate_under_test", ROOT / "scripts" / "ledger_iso8601_gate.py"
)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = gate  # dataclasses resolve annotations via sys.modules
spec.loader.exec_module(gate)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")

GOOD = "2026-10-30T13:02:24-04:00"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _put(repo: Path, rel: str, obj) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _put(tmp_path, "ledger/0001.yaml", {"entry_index": 1, "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-24"})
    _put(tmp_path, "ledger.v2/9241.yml", {"entry_index": 9241, "timestamp": "2026-09-14Z"})
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def _base(repo: Path) -> str:
    return _git(repo, "rev-list", "--max-parents=0", "HEAD")


def _commit(repo: Path, msg: str = "add") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _run(repo, capsys, *extra):
    code = gate.main(["--repo", str(repo), "--base", _base(repo), "--json", *extra])
    cap = capsys.readouterr()
    return code, (json.loads(cap.out) if cap.out.strip() else None), cap.err


@pytest.mark.parametrize("value", [
    GOOD, "2026-10-30T17:02:24Z", "2026-10-30T13:02-04:00", "2026-10-30T13:02:24.123456+05:30",
])
def test_iso_with_offset_accepted(value):
    assert gate.is_iso8601_with_offset(value)


@pytest.mark.parametrize("value", [
    "ETERNAL_NOW_ANCHORED_TO_2026-08-24", "2026-09-14Z", "2026-10-30", "2026-10-30T13:02:24",
    "2026-10-30 13:02:24-04:00", "2026-10-30T13:02:24-0400", "2026-13-40T25:61:00Z", None, 20261030,
])
def test_non_iso_or_offsetless_rejected(value):
    assert not gate.is_iso8601_with_offset(value)


def test_no_new_entries_legacy_report_only(repo, capsys):
    code, data, _ = _run(repo, capsys)
    assert code == 0
    assert data["new_entries"] == 0
    assert {r["path"] for r in data["legacy_report_only"]} == {"ledger/0001.yaml", "ledger.v2/9241.yml"}


def test_new_committed_entry_valid_passes(repo, capsys):
    _put(repo, "ledger.v2/9400.yml", {"entry_index": 9400, "timestamp": GOOD, "sealed_at": "2026-10-30T17:02:24Z"})
    _commit(repo)
    code, data, _ = _run(repo, capsys)
    assert code == 0
    assert data["new_passing"] == ["ledger.v2/9400.yml"]
    assert len(data["legacy_report_only"]) == 2  # legacy never fails


def test_new_committed_entry_non_iso_fails(repo, capsys):
    _put(repo, "ledger.v2/9400.yml", {"entry_index": 9400, "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-10-30"})
    _commit(repo)
    code, data, _ = _run(repo, capsys)
    assert code == 1
    assert data["new_failing"][0]["path"] == "ledger.v2/9400.yml"


def test_new_entry_missing_timestamp_fails(repo, capsys):
    _put(repo, "ledger/9401.yaml", {"entry_index": 9401})
    _commit(repo)
    code, data, _ = _run(repo, capsys)
    assert code == 1
    assert "missing required `timestamp`" in data["new_failing"][0]["problems"][0]


def test_nested_at_field_without_offset_fails(repo, capsys):
    _put(repo, "ledger/9402.yaml", {"timestamp": GOOD, "witness": {"signed_at": "2026-10-30T13:02:24"}})
    _commit(repo)
    code, data, _ = _run(repo, capsys)
    assert code == 1
    assert "witness.signed_at" in data["new_failing"][0]["problems"][0]


def test_untracked_and_staged_new_entries_are_checked(repo, capsys):
    _put(repo, "ledger/9403.yaml", {"timestamp": "2026-10-30"})
    code, _, _ = _run(repo, capsys)
    assert code == 1
    _git(repo, "add", "ledger/9403.yaml")
    code, _, _ = _run(repo, capsys)
    assert code == 1


def test_modified_legacy_entry_is_not_new(repo, capsys):
    _put(repo, "ledger/0001.yaml", {"entry_index": 1, "timestamp": "still not iso"})
    _commit(repo)
    code, data, _ = _run(repo, capsys)
    assert code == 0 and data["new_entries"] == 0


def test_base_from_env(repo, capsys, monkeypatch):
    _put(repo, "ledger/9404.yaml", {"timestamp": "bad"})
    _commit(repo)
    monkeypatch.setenv(gate.BASE_ENV, _git(repo, "rev-parse", "HEAD"))
    code = gate.main(["--repo", str(repo), "--json"])
    capsys.readouterr()
    assert code == 0  # 9404 is legacy relative to the env base


def test_unknown_base_is_usage_error(repo, capsys):
    code, _, err = _run(repo, capsys, "--base", "0" * 40)
    assert code == 2 and "git" in err


def test_new_unparsable_entry_exits_2(repo, capsys):
    _put(repo, "ledger/9405.yaml", [1, 2])  # parses, but is not a mapping
    _commit(repo)
    code, data, _ = _run(repo, capsys)
    assert code == 2 and data["new_unparsed"][0]["path"] == "ledger/9405.yaml"


def test_yaml_missing_with_yaml_files_exits_2(repo, capsys, monkeypatch):
    monkeypatch.setitem(sys.modules, "yaml", None)
    _put(repo, "ledger/9406.yaml", "timestamp: '2026-10-30T13:02:24-04:00'\n")
    code, data, err = _run(repo, capsys)
    assert code == 2 and data is None
    assert "PyYAML is not importable" in err
