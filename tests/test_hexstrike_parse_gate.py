# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""hexstrike must not pass a scan it could not read.

Fixtures are JSON-format entries in temp dirs, so these run under
`python -I -m pytest` without PyYAML. The yaml-missing case is simulated by
blocking `import yaml` with sys.modules.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod  # dataclasses resolve annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


hexstrike = _load("hexstrike_under_test", "scripts/hexstrike.py")
prebuild = _load("prebuild_under_test", "scripts/prebuild.py")

YAML_ONLY = "entry_index: 7\nseal: abc\nstatus: SEALED\nnote: plain YAML, not JSON\n"


def _write(root: Path, name: str, obj) -> Path:
    p = root / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return p


def _clean_entry(i: int) -> dict:
    payload = {"entry_index": i, "body": "ok"}
    return {"entry_index": i, "payload": payload, "seal": hexstrike.compute_seal(payload)}


@pytest.fixture
def no_yaml(monkeypatch):
    monkeypatch.setitem(sys.modules, "yaml", None)  # import yaml -> ImportError


def _main_json(capsys, *argv) -> tuple[int, dict, str]:
    code = hexstrike.main([*map(str, argv), "--json"])
    cap = capsys.readouterr()
    return code, json.loads(cap.out), cap.err


def test_clean_json_ledger_exits_0(tmp_path, capsys):
    _write(tmp_path, "0001.yaml", _clean_entry(1))
    code, data, _ = _main_json(capsys, tmp_path)
    assert code == 0
    assert data["metrics"]["unparsed"] == 0
    assert data["parse_failures"] == []


def test_exit_1_semantics_unchanged(tmp_path, capsys):
    _write(tmp_path, "0001.yaml", {"entry_index": 1, "seal": "LABEL · SEALED"})
    bad = _clean_entry(2)
    bad["seal"] = "0" * 64
    _write(tmp_path, "0002.yaml", bad)
    code, data, _ = _main_json(capsys, tmp_path)
    assert code == 1
    assert data["metrics"]["by_kind"] == {"empty_payload": 1, "forged_seal": 1}


def test_seal_computation_unchanged():
    payload = {"b": 1, "a": [1, 2]}
    import hashlib

    want = hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    assert hexstrike.compute_seal(payload) == want


def test_unparsable_entry_exits_2_and_is_recorded(tmp_path, capsys):
    _write(tmp_path, "0001.yaml", _clean_entry(1))
    _write(tmp_path, "0002.yaml", "{ not: [valid")
    code, data, err = _main_json(capsys, tmp_path)
    assert code == 2
    assert data["metrics"]["unparsed"] == 1
    assert data["metrics"]["blocking_unparsed"] == 1
    (pf,) = data["parse_failures"]
    assert pf["path"].endswith("0002.yaml") and pf["known"] is False
    assert "INCOMPLETE SCAN -- 1 of 2" in err


def test_non_mapping_entry_exits_2(tmp_path, capsys):
    _write(tmp_path, "0001.yaml", [1, 2, 3])
    code, data, _ = _main_json(capsys, tmp_path)
    assert code == 2
    assert data["parse_failures"][0]["reason"] == "not_a_mapping"


def test_yaml_missing_with_yaml_files_exits_2(tmp_path, capsys, no_yaml):
    _write(tmp_path, "0001.yaml", YAML_ONLY)
    _write(tmp_path, "0002.yaml", YAML_ONLY)
    code, data, err = _main_json(capsys, tmp_path)
    assert code == 2, "ghost pass: unparsed YAML must not report a pass"
    assert data["yaml_available"] is False
    assert data["metrics"]["parsed"] == 0 and data["metrics"]["findings"] == 0
    assert {pf["reason"] for pf in data["parse_failures"]} == {"yaml_unavailable"}
    assert "2 of 2" in err and "PyYAML is not importable" in err


def test_yaml_missing_but_json_entries_still_scan(tmp_path, capsys, no_yaml):
    _write(tmp_path, "0001.yaml", _clean_entry(1))
    code, data, _ = _main_json(capsys, tmp_path)
    assert code == 0 and data["metrics"]["parsed"] == 1


def _known_list(repo: Path, rel: str) -> Path:
    (repo / "scripts").mkdir(exist_ok=True)
    lst = repo / "scripts" / "known.txt"
    lst.write_text(f"# header\n{rel}  # malformed, append-only\n", encoding="utf-8")
    return lst


def test_known_unparsed_list_downgrades_listed_parse_error(tmp_path, capsys):
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    _write(ledger, "0001.yaml", _clean_entry(1))
    _write(ledger, "0002.yaml", [1, 2])  # parses (JSON or YAML) but is not a mapping
    lst = _known_list(tmp_path, "ledger/0002.yaml")
    code, data, _ = _main_json(capsys, ledger, "--known-unparsed", lst)
    assert code == 0
    assert data["metrics"]["known_unparsed"] == 1
    assert data["parse_failures"][0]["known"] is True
    # still reported in text output
    assert hexstrike.main([str(ledger), "--known-unparsed", str(lst)]) == 0
    assert "KNOWN-UNPARSED" in capsys.readouterr().out


def test_known_list_never_excuses_missing_yaml(tmp_path, capsys, no_yaml):
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    _write(ledger, "0002.yaml", YAML_ONLY)
    lst = _known_list(tmp_path, "ledger/0002.yaml")
    code, data, _ = _main_json(capsys, ledger, "--known-unparsed", lst)
    assert code == 2
    assert data["metrics"]["known_unparsed"] == 0


def test_known_list_missing_file_is_usage_error(tmp_path, capsys):
    _write(tmp_path, "0001.yaml", _clean_entry(1))
    assert hexstrike.main([str(tmp_path), "--known-unparsed", str(tmp_path / "nope")]) == 2


def test_committed_known_list_names_only_9128():
    lst = ROOT / "scripts" / "hexstrike_known_unparsed.txt"
    known = hexstrike.load_known_unparsed(lst)
    assert list(known) == [str((ROOT / "ledger" / "9128.yaml").resolve())]


def test_prebuild_hexstrike_stage_fails_on_incomplete_scan(tmp_path):
    _write(tmp_path, "0001.yaml", "{ not: [valid")
    s = prebuild.stage_hexstrike(tmp_path)
    assert s.status == "fail"
    assert "INCOMPLETE SCAN" in s.detail


def test_prebuild_hexstrike_stage_passes_clean(tmp_path):
    _write(tmp_path, "0001.yaml", _clean_entry(1))
    s = prebuild.stage_hexstrike(tmp_path)
    assert s.status == "pass", s.detail


def test_prebuild_runs_iso8601_after_hexstrike(monkeypatch, tmp_path):
    names = [s.name for s in prebuild.run([], tmp_path / "absent")]
    assert names.index("ledger_iso8601") == names.index("hexstrike") + 1
