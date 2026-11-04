# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Offline tests for tools/ledger_index.py + tools/ledger_seal.py (run: python -I -m pytest)."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ledger_index  # noqa: E402
import ledger_seal  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _entry(n, event="X"):
    d = {"entry_index": n, "event": event, "nullify_ban": 10.06,
         "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-07-30T00:00:00Z"}
    d["seal"] = "∀∞φ² · X · " + ledger_seal.regime_b(d, n)
    return d


def _tree(tmp_path, entries):
    import yaml
    for folder, name, d in entries:
        (tmp_path / folder).mkdir(exist_ok=True)
        (tmp_path / folder / name).write_text(yaml.safe_dump(d, allow_unicode=True) if isinstance(d, dict) else d,
                                              encoding="utf-8")
    return tmp_path


def test_regime_b_verifies_and_tamper_is_unverified():
    d = _entry(9300)
    assert ledger_seal.verify_entry(d)["status"] == "verified"
    d["event"] = "Y"
    assert ledger_seal.verify_entry(d)["status"] == "unverified"


def test_no_digest_is_never_a_pass():
    assert ledger_seal.verify_entry({"entry_index": 1, "event": "x"})["status"] == "no_declared_digest"


def test_seal_sha3_256_mismatch_is_hard_unverified():
    d = _entry(9300)
    d["seal_sha3_256"] = "0" * 64
    v = ledger_seal.verify_entry(d)
    assert v["status"] == "unverified" and v["regimes"] == []


def test_regime_s_matches_ci_seals_verifier():
    seals = _load(".github/scripts/verify_ledger_seals.py", "vls")
    d = {"entry_index": 8973, "event": "E", "x": "φ"}
    d["seal_sha3_256"] = seals.expected_digest(d)
    assert ledger_seal.verify_entry(d)["status"] == "verified"


def test_aliases_timestamp_and_flags(tmp_path):
    root = _tree(tmp_path, [("ledger", "9300.yaml", _entry(9300)),
                            ("ledger.v2", "9300.yml", _entry(9300)),
                            ("ledger", "510510.yaml", _entry(510510)),
                            ("ledger", "9301.yaml", "a: [unclosed\n")])
    rows = ledger_index.build_index(root)
    by = {r["path"]: r for r in rows}
    r = by["ledger/9300.yaml"]
    assert r["null_ban"] == 10.06 and r["field_aliases"]["null_ban"] == "nullify_ban"
    assert r["timestamp"] == "2026-07-30T00:00:00Z" and r["raw"]["nullify_ban"] == 10.06
    assert "duplicate_index_cross_folder" in r["flags"]
    assert "outlier_index" in by["ledger/510510.yaml"]["flags"]
    bad = by["ledger/9301.yaml"]
    assert "parse_error" in bad["flags"] and bad["seal_status"] == "unverified"
    keys = [(x["entry_index"], x["folder"], x["path"]) for x in rows]
    assert keys == sorted(keys)


def test_chain_append_only_and_tamper_detected(tmp_path):
    root = _tree(tmp_path, [("ledger", "9300.yaml", _entry(9300))])
    assert ledger_index.main(["--root", str(root)]) == 0
    first = (root / "ledger.chain.jsonl").read_text()
    assert ledger_index.main(["--root", str(root), "--check"]) == 0
    _tree(root, [("ledger", "9299.yaml", _entry(9299))])  # lower index, appended later
    assert ledger_index.main(["--root", str(root), "--check"]) == 1  # stale
    assert ledger_index.main(["--root", str(root)]) == 0
    chain = (root / "ledger.chain.jsonl").read_text()
    assert chain.startswith(first)  # append-only
    lines = [json.loads(l) for l in chain.splitlines()]
    assert lines[1]["prev_hash"] == lines[0]["sha256"] and lines[0]["prev_hash"] == "0" * 64
    (root / "ledger" / "9300.yaml").write_text("tampered: true\n")
    assert ledger_index.main(["--root", str(root), "--check"]) == 1


def test_committed_index_and_chain_are_current():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "ledger_index.py"),
                        "--root", str(ROOT), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_three_verifiers_agree_on_sample():
    rows = {r["path"]: r for r in map(json.loads, (ROOT / "ledger_index.jsonl").open(encoding="utf-8"))}
    for p in ("ledger/8216.yaml", "ledger/8217.yaml", "ledger/9259.yaml"):
        if p not in rows:
            continue
        r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "verify_ledger.py"),
                            str(ROOT / p), "--verify-seal"], capture_output=True, text=True)
        assert (r.returncode == 0) == (rows[p]["seal_status"] == "verified"), p
