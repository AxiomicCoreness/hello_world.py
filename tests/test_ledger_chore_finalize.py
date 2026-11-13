import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "ledger_chore_finalize.py"


def _run(cwd, *args):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=False)


@pytest.fixture()
def repo(tmp_path):
    for d in ("ledger", "ledger.v2", "tools"):
        shutil.copytree(ROOT / d, tmp_path / d)
    for f in ("ledger_index.jsonl", "ledger.chain.jsonl"):
        shutil.copy2(ROOT / f, tmp_path / f)
    _run(tmp_path, "git", "init", "-q")
    _run(tmp_path, "git", "add", "-A")
    _run(tmp_path, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    return tmp_path


def _finalize(repo):
    return _run(repo, sys.executable, "-I", str(repo / "tools" / "ledger_chore_finalize.py"), "--root", ".")


@needs_git
def test_rewrite_of_chained_entry_is_discarded(repo):
    p = repo / "ledger" / "8226.yaml"
    before = p.read_bytes()
    p.write_text(p.read_text(encoding="utf-8").replace("2026-10-07T19:50:53Z", "2099-01-01T00:00:00Z"),
                 encoding="utf-8")
    r = _finalize(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "rewrite discarded" in r.stdout
    assert p.read_bytes() == before
    assert "OK: index current, chain unbroken" in r.stdout


@needs_git
def test_new_entry_gets_prev_hash_and_chain_link(repo):
    chain_before = (repo / "ledger.chain.jsonl").read_text(encoding="utf-8").splitlines()
    new = repo / "ledger.v2" / "99990.yml"
    new.write_text("entry_index: 99990\nevent: /chore_test\nprev_hash: ''\n"
                   "seal: ∀∞φ² · CHORE_TEST · SEALED · " + "ab" * 32 + "\n", encoding="utf-8")
    r = _finalize(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    d = yaml.safe_load(new.read_text(encoding="utf-8"))
    files = sorted((repo / "ledger").glob("*.yaml")) + sorted((repo / "ledger.v2").glob("*.yml"))
    best = None
    for f in files:
        if f == new:
            continue
        try:
            e = yaml.safe_load(f.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            e = None
        if not isinstance(e, dict) or not isinstance(e.get("entry_index"), int) or e["entry_index"] >= 99990:
            continue
        m = re.findall(r"[0-9a-f]{64}", str(e.get("seal", "")).lower())
        if m and (best is None or e["entry_index"] > best[0]):
            best = (e["entry_index"], m[-1])
    assert d["prev_hash"] == best[1]
    chain_after = (repo / "ledger.chain.jsonl").read_text(encoding="utf-8").splitlines()
    assert chain_after[:len(chain_before)] == chain_before
    last = json.loads(chain_after[-1])
    assert last["path"] == "ledger.v2/99990.yml"
    assert last["sha256"] == hashlib.sha256(new.read_bytes()).hexdigest()


def test_8226_is_create_only_in_cd_combinator():
    t = (ROOT / ".github" / "workflows" / "cd-combinator.yml").read_text(encoding="utf-8")
    assert 'if [ -e ledger/8226.yaml ]' in t
    assert 'path.open("x"' in t
    assert "steps.plan.outputs.write == 'true'" in t
    assert "ledger_chore_finalize.py" in t
