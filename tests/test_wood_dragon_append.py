# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Wood-dragon dispatch appends a new ledger entry and never rewrites one."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "wood-dragon-dispatch.yml"
SCRIPT = ROOT / ".github" / "scripts" / "wood_dragon_append.py"


def _load():
    spec = importlib.util.spec_from_file_location("wood_dragon_append", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(directory: Path, name: str, doc) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    if isinstance(doc, str):
        path.write_text(doc, encoding="utf-8")
    else:
        path.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return path


def _dispatch(module, ledger: Path, preferred: int = 9007, **kwargs):
    defaults = dict(
        event="/workflow_dispatch_wood_dragon_mistral",
        terminal_count=3,
        last_observed=26,
        i_of_144="1",
        mcp_contract_ok="true",
        mcp_url="",
        mcp_port="13800",
        mcp_namespace="wood-dragon-dispatch",
        terminals_json="[]",
        hash_algo="sha3_256",
        also_dir=None,
    )
    defaults.update(kwargs)
    return module.append_dispatch(ledger, preferred, **defaults)


def test_free_preferred_is_created_and_verifies(tmp_path):
    module = _load()
    ledger = tmp_path / "ledger"
    result = _dispatch(module, ledger, 9007)
    assert result["entry_index"] == 9007
    assert result["appended"] is False
    path = ledger / "9007.yaml"
    assert path.is_file()
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["entry_index"] == 9007
    assert doc["witness"] == "GENESIS → 9007 — UNBROKEN"
    assert doc["grava_star_fired"] is False
    verified = subprocess.run(
        [sys.executable, "-I", str(ROOT / ".github" / "scripts" / "verify_ledger.py"),
         "--mode", "hard", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr


def test_occupied_preferred_appends_without_touching_bytes(tmp_path):
    module = _load()
    ledger = tmp_path / "ledger"
    v2 = tmp_path / "ledger.v2"
    first = _write(ledger, "9007.yaml", "entry_index: 9007\nseal: keep-me\n")
    second = _write(ledger, "9008.yaml", "entry_index: 9008\nseal: also\n")
    # 9009 is taken in the other tree, so the next free slot after the head is 9010.
    blocked = _write(v2, "9009.yml", "entry_index: 9009\nseal: v2\n")
    before = {first: _sha(first), second: _sha(second), blocked: _sha(blocked)}
    result = _dispatch(module, ledger, 9007, also_dir=v2)
    assert result["entry_index"] == 9010
    assert result["appended"] is True
    assert result["prev_index"] == 9009
    assert result["witness"] == "9009 → 9010 — UNBROKEN"
    assert {path: _sha(path) for path in before} == before
    created = ledger / "9010.yaml"
    doc = yaml.safe_load(created.read_text(encoding="utf-8"))
    assert doc["entry_index"] == 9010
    assert doc["prev_hash"] == ""
    assert not (v2 / "9010.yml").exists()
    again = _dispatch(module, ledger, 9007, also_dir=v2)
    assert again["entry_index"] == 9011
    assert _sha(created) == hashlib.sha256(created.read_bytes()).hexdigest()
    assert _sha(first) == before[first]


def test_high_index_uses_regime_b_and_chain_appends(tmp_path):
    module = _load()
    sys.path.insert(0, str(ROOT / "tools"))
    import ledger_index
    import ledger_seal

    ledger = tmp_path / "ledger"
    preferred = _write(ledger, "9007.yaml", "entry_index: 9007\nseal: keep\n")
    prev_doc = {
        "entry_index": 9311,
        "event": "/previous",
        "seal": "∀∞φ² · PREV · SEALED · " + ("ab" * 32),
    }
    prev = _write(ledger, "9311.yaml", prev_doc)
    before = {_sha(preferred), _sha(prev)}
    result = _dispatch(module, ledger, 9007)
    assert result["entry_index"] == 9312
    assert result["prev_hash"] == "ab" * 32
    assert result["witness"] == "9311 → 9312 — UNBROKEN"
    assert {_sha(preferred), _sha(prev)} == before
    new = ledger / "9312.yaml"
    doc = yaml.safe_load(new.read_text(encoding="utf-8"))
    assert ledger_seal.regime_b(doc, 9312) == ledger_seal.declared_hex(doc)
    verified = subprocess.run(
        [sys.executable, "-I", str(ROOT / ".github" / "scripts" / "verify_ledger.py"),
         "--mode", "hard", str(new)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr

    assert ledger_index.main(["--root", str(tmp_path)]) == 0
    chain_before = (tmp_path / "ledger.chain.jsonl").read_text(encoding="utf-8")
    # A second append must extend the chain file, not rewrite the first link.
    _dispatch(module, ledger, 9007)
    assert ledger_index.main(["--root", str(tmp_path)]) == 0
    chain_after = (tmp_path / "ledger.chain.jsonl").read_text(encoding="utf-8")
    assert chain_after.startswith(chain_before)
    assert ledger_index.main(["--root", str(tmp_path), "--check"]) == 0
    rows = [json.loads(line) for line in chain_after.splitlines()]
    assert [row["path"] for row in rows] == [
        "ledger/9007.yaml",
        "ledger/9311.yaml",
        "ledger/9312.yaml",
        "ledger/9313.yaml",
    ]
    assert rows[2]["prev_hash"] == rows[1]["sha256"]
    assert {_sha(preferred), _sha(prev)} == before
    assert _sha(new) == hashlib.sha256(new.read_bytes()).hexdigest()


def test_cli_on_temp_copy_does_not_overwrite(tmp_path):
    source = ROOT / "ledger" / "9007.yaml"
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    copied = ledger / "9007.yaml"
    copied.write_bytes(source.read_bytes())
    before = copied.read_bytes()
    proc = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--ledger-dir", str(ledger), "--preferred", "9007"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    assert copied.read_bytes() == before
    created = list(ledger.glob("*.yaml"))
    assert len(created) == 2
    new = next(path for path in created if path.name != "9007.yaml")
    assert new.name == "9008.yaml"
    doc = yaml.safe_load(new.read_text(encoding="utf-8"))
    assert doc["entry_index"] == 9008
    assert "9007 → 9008" in doc["witness"]


def test_workflow_appends_instead_of_rewriting_9007():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "inputs:" in text
    assert "event:" in text
    assert "i_of_144:" in text
    assert "wood_dragon_append.py" in text
    assert "tools/ledger_index.py --root ." in text
    assert "tools/ledger_index.py --root . --check" in text
    assert "path.write_text" not in text
    assert "file_pattern: ledger/9007.yaml" not in text
    assert 'DISPATCH_ENTRY: "9007"' in text
    doc = yaml.safe_load(text)
    on = doc.get(True) or doc.get("on")
    assert "workflow_dispatch" in on
    inputs = on["workflow_dispatch"]["inputs"]
    assert "event" in inputs and "i_of_144" in inputs
