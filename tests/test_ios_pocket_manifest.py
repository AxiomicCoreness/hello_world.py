# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""tools/ios_pocket_manifest.py: deterministic manifest + append-only ledger.v2 entry.

Offline. Each test builds a throwaway git repo in a temp dir. Runs under
`python -I -m pytest`; the verify_ledger.py acceptance tests need PyYAML and
are skipped (visibly) without it.
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


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


mf = _load("ios_pocket_manifest_under_test", ROOT / "tools" / "ios_pocket_manifest.py")

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")

PREV_EVENT = "/model_pinning_and_release_verification"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _write(repo: Path, rel: str, data: bytes) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def _prev_entry_text(n: int = 9307) -> str:
    h = mf.event_hash(n, PREV_EVENT)
    return (f"entry_index: {n}\nevent: {PREV_EVENT}\nstatus: SEALED\n"
            f"timestamp: '2026-10-30T14:53:42-04:00'\nhash_algo: sha3_256\n"
            f"prev_hash: {'f' * 64}\nwitness_chain: {n - 1} -> {n}\n"
            f"terminal_hex: {h}\nseal: ∀∞φ² · X_{n} · WOOD_DRAGON_0.91 · SEALED · {h}\n"
            f"seal_sha3_256: {h}\n")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _write(r, "ios/ClarkePocket/b.swift", b"let b = 2\n")
    _write(r, "ios/ClarkePocket/A/z.swift", b"// z\n")
    _write(r, "ios/ClarkePocket/empty.txt", b"")
    _write(r, "ios/ClarkePocket/caf\u00e9.md", "caf\u00e9\n".encode())
    _write(r, "ios/ClarkePocket/run.sh", b"#!/bin/sh\necho hi\n")
    (r / "ios/ClarkePocket/run.sh").chmod(0o755)
    _write(r, "ios/Other/x.swift", b"outside\n")
    _write(r, "ios/ClarkePocketExtra/y.swift", b"sibling prefix, outside\n")
    _write(r, "ledger.v2/9306.yml", _prev_entry_text(9306).encode())
    _write(r, "ledger.v2/9307.yml", _prev_entry_text(9307).encode())
    _write(r, "ledger.v2/README.md", b"not an entry\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _run_json(tmp_path: Path, sha: str, **over) -> Path:
    d = {"id": 41230335813, "run_attempt": 1, "event": "push", "head_branch": "main",
         "head_sha": sha, "status": "completed", "conclusion": "success",
         "updated_at": "2026-10-31T18:39:06Z",
         "path": ".github/workflows/ios-pocket-simulator.yml",
         "html_url": "https://github.com/AxiomicCoreness/hello_world.py/actions/runs/41230335813"}
    d.update(over)
    p = tmp_path / f"run-{len(over)}-{hashlib.sha256(json.dumps(over).encode()).hexdigest()[:8]}.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


def _entry(repo: Path, tmp_path: Path, *extra: str, run=None) -> int:
    sha = _head(repo)
    return mf.main(["entry", "--repo", str(repo), "--rev", sha,
                    "--ios-run-json", str(run or _run_json(tmp_path, sha)),
                    "--ledger-main", sha, "--timestamp", "2026-10-31T18:45:00Z", *extra])


# ── manifest ───────────────────────────────────────────────────────────────
def test_manifest_matches_independent_recompute(repo: Path):
    m = mf.build_manifest(repo, "HEAD")
    paths = [f["path"] for f in m["files"]]
    assert paths == sorted(paths, key=lambda p: p.encode("utf-8"))
    assert set(paths) == {
        "ios/ClarkePocket/A/z.swift", "ios/ClarkePocket/b.swift",
        "ios/ClarkePocket/caf\u00e9.md", "ios/ClarkePocket/empty.txt",
        "ios/ClarkePocket/run.sh",
    }
    lines = []
    for p in paths:
        data = (repo / p).read_bytes()
        mode = "100755" if p.endswith("run.sh") else "100644"
        lines.append(f"{hashlib.sha256(data).hexdigest()} {len(data)} {mode} {p}\n")
    listing = "".join(lines).encode("utf-8")
    assert m["tree_root_sha256"] == hashlib.sha256(listing).hexdigest()
    assert m["tree_root_sha3_256"] == hashlib.sha3_256(listing).hexdigest()
    assert m["file_count"] == 5
    assert m["total_bytes"] == sum(len((repo / p).read_bytes()) for p in paths)
    assert len(m["commit"]) == 40 and len(m["git_tree"]) == 40
    empty = next(f for f in m["files"] if f["path"].endswith("empty.txt"))
    assert empty["size"] == 0 and empty["sha256"] == hashlib.sha256(b"").hexdigest()


def test_manifest_reads_git_objects_not_working_tree(repo: Path):
    before = mf.build_manifest(repo, "HEAD")
    _write(repo, "ios/ClarkePocket/b.swift", b"dirty edit\n")
    _write(repo, "ios/ClarkePocket/untracked.swift", b"new\n")
    assert mf.build_manifest(repo, "HEAD") == before
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "change")
    after = mf.build_manifest(repo, "HEAD")
    assert after["tree_root_sha256"] != before["tree_root_sha256"]
    assert after["file_count"] == 6
    assert mf.build_manifest(repo, before["commit"]) == before  # by SHA, any time


def test_manifest_cli_json_is_deterministic(repo: Path, capsys):
    outs = []
    for _ in range(2):
        assert mf.main(["manifest", "--repo", str(repo), "--rev", "HEAD"]) == 0
        outs.append(capsys.readouterr().out)
    assert outs[0] == outs[1]
    assert json.loads(outs[0])["format"] == "IOS.POCKET.MANIFEST.v1"


def test_manifest_refuses_empty_prefix(repo: Path):
    with pytest.raises(mf.ManifestError):
        mf.build_manifest(repo, "HEAD", "ios/DoesNotExist")


# ── plan / numbering ───────────────────────────────────────────────────────
def test_plan_chains_to_last_entry(repo: Path):
    m = mf.build_manifest(repo, "HEAD")
    pl = mf.plan(repo, repo / "ledger.v2", m)
    assert pl["next_index"] == 9308 and pl["prev_index"] == 9307
    assert pl["prev_hash"] == mf.event_hash(9307, PREV_EVENT)
    assert pl["previous_ios_entry"] is None and pl["unchanged"] is False


def test_plan_collision_with_pending_pr_fails_clearly(repo: Path, tmp_path: Path, capsys):
    rc = _entry(repo, tmp_path, "--taken", "9308")
    assert rc == mf.EXIT_TAKEN
    err = capsys.readouterr().err
    assert "collision" in err and "9308" in err
    assert not (repo / "ledger.v2" / "9308.yml").exists()


def test_plan_collision_with_flat_root(repo: Path, tmp_path: Path):
    _write(repo, "ledger/9308.yaml", b"entry_index: 9308\n")
    assert _entry(repo, tmp_path) == mf.EXIT_TAKEN


def test_plan_refuses_duplicate_index(repo: Path):
    _write(repo, "ledger.v2/9307b.yml", _prev_entry_text(9307).encode())  # not NNNN.yml: ignored
    _write(repo, "ledger.v2/09307.yml", _prev_entry_text(9307).encode())
    with pytest.raises(mf.ManifestError, match="duplicate"):
        mf.plan(repo, repo / "ledger.v2", mf.build_manifest(repo, "HEAD"))


# ── entry ──────────────────────────────────────────────────────────────────
def test_entry_written_sealed_and_chained(repo: Path, tmp_path: Path):
    assert _entry(repo, tmp_path) == 0
    p = repo / "ledger.v2" / "9308.yml"
    text = p.read_text(encoding="utf-8")
    sha = _head(repo)
    event = "/ios_clarke_pocket_manifest_" + sha
    want = hashlib.sha3_256(
        b"GARDEN.EVENT.v1.LEDGER\x00"
        + f"9308|{event}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462".encode("ascii")
    ).hexdigest()
    sc = mf._top_scalars(text)
    assert sc["entry_index"] == "9308" and sc["event"] == event
    assert sc["seal_sha3_256"] == want and sc["terminal_hex"] == want
    assert sc["seal"].endswith("· " + want)
    assert sc["prev_hash"] == mf.event_hash(9307, PREV_EVENT)
    assert sc["witness_chain"] == "9307 -> 9308"
    assert sc["measured_at_commit"] == sha
    assert sc["timestamp"] in ("2026-10-31T14:45:00-04:00", "2026-10-31T18:45:00+00:00")
    assert "completed_at: \"2026-10-31T14:39:06-04:00\"" in text or "+00:00" in text
    assert "PENDING" not in text.upper()
    assert mf.manifest_block(mf.build_manifest(repo, sha)) in text
    # append-only: the predecessor is byte-identical, and a second write refuses
    assert (repo / "ledger.v2" / "9307.yml").read_text(encoding="utf-8") == _prev_entry_text(9307)
    assert _entry(repo, tmp_path, "--out", str(p)) == mf.EXIT_UNCHANGED


def test_entry_refuses_overwrite(repo: Path, tmp_path: Path):
    out = repo / "ledger.v2" / "9308.yml"
    out.write_text("keep me\n", encoding="utf-8")
    assert _entry(repo, tmp_path) == mf.EXIT_TAKEN
    assert out.read_text(encoding="utf-8") == "keep me\n"


def test_unchanged_tree_is_not_recorded_twice(repo: Path, tmp_path: Path, capsys):
    assert _entry(repo, tmp_path) == 0
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "ledger 9308")  # ledger-only change; ios tree same
    capsys.readouterr()
    assert _entry(repo, tmp_path) == mf.EXIT_UNCHANGED
    assert "nothing to record" in capsys.readouterr().err
    _write(repo, "ios/ClarkePocket/b.swift", b"let b = 3\n")
    _git(repo, "commit", "-qam", "ios change")
    assert _entry(repo, tmp_path) == 0
    text = (repo / "ledger.v2" / "9309.yml").read_text(encoding="utf-8")
    assert "previous_ios_entry: 9308" in text
    assert mf._top_scalars(text)["prev_hash"] == mf._top_scalars(
        (repo / "ledger.v2" / "9308.yml").read_text(encoding="utf-8"))["seal_sha3_256"]


@pytest.mark.parametrize("over", [
    {"head_sha": "0" * 40},
    {"conclusion": "failure"},
    {"status": "in_progress"},
    {"event": "pull_request"},
    {"head_branch": "feature"},
    {"path": ".github/workflows/ios-clarke-pocket.yml"},
])
def test_entry_refuses_unverified_ci(repo: Path, tmp_path: Path, over):
    run = _run_json(tmp_path, _head(repo), **over)
    assert _entry(repo, tmp_path, run=run) == mf.EXIT_EVIDENCE
    assert not (repo / "ledger.v2" / "9308.yml").exists()


def test_timestamps_need_offset(repo: Path, tmp_path: Path):
    sha = _head(repo)
    rc = mf.main(["entry", "--repo", str(repo), "--rev", sha,
                  "--ios-run-json", str(_run_json(tmp_path, sha)),
                  "--ledger-main", sha, "--timestamp", "2026-10-31T18:45:00"])
    assert rc == mf.EXIT_USAGE


# ── check-entry ────────────────────────────────────────────────────────────
def test_check_entry_roundtrip_and_tamper(repo: Path, tmp_path: Path):
    assert _entry(repo, tmp_path) == 0
    p = repo / "ledger.v2" / "9308.yml"
    assert mf.check_entry(repo, p, repo / "ledger.v2") == []
    text = p.read_text(encoding="utf-8")
    m = mf.build_manifest(repo, _head(repo))
    victim = m["files"][0]["sha256"]
    p.write_text(text.replace(victim, "0" * 64, 1), encoding="utf-8")
    assert any("manifest block" in x for x in mf.check_entry(repo, p, repo / "ledger.v2"))
    p.write_text(text.replace(mf.event_hash(9307, PREV_EVENT), "e" * 64, 1), encoding="utf-8")
    assert any("prev_hash" in x for x in mf.check_entry(repo, p, repo / "ledger.v2"))


# ── acceptance by the existing verifiers (needs PyYAML) ────────────────────
def test_existing_verify_ledger_accepts_entry(repo: Path, tmp_path: Path, capsys):
    yaml = pytest.importorskip("yaml")
    vl = _load("verify_ledger_under_test", ROOT / ".github" / "scripts" / "verify_ledger.py")
    assert _entry(repo, tmp_path) == 0
    p = repo / "ledger.v2" / "9308.yml"
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    for k in ("prev_hash", "measured_at_commit", "seal_sha3_256", "terminal_hex", "timestamp"):
        assert isinstance(d[k], str), k
    assert len(d["payload"]["ios_clarke_pocket"]["files"]) == 5
    capsys.readouterr()
    assert vl.verify(p, "hard") is True
    assert "regime=B(event)" in capsys.readouterr().out
    assert vl.sealed_concrete_violations(d, 9308) == []
    assert vl.entry_declared_digest(d) == d["seal_sha3_256"]
    prev = yaml.safe_load((repo / "ledger.v2" / "9307.yml").read_text(encoding="utf-8"))
    assert d["prev_hash"] == vl.entry_declared_digest(prev)


def test_chains_onto_real_ledger_tip(repo: Path, tmp_path: Path):
    real = ROOT / "ledger.v2"
    if not any(real.glob("*.yml")):
        pytest.skip("no ledger.v2 entries in this checkout")
    copy = tmp_path / "ledger.v2"
    shutil.copytree(real, copy)
    last = max(mf.read_ledger(copy), key=lambda e: e["index"])
    pl = mf.plan(repo, copy, mf.build_manifest(repo, "HEAD"))
    assert pl["next_index"] == last["index"] + 1
    assert pl["prev_hash"] == mf.declared_digest(last["scalars"])
    assert len(pl["prev_hash"]) == 64
