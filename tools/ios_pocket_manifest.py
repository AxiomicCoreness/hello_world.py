#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""ios_pocket_manifest.py — hash manifest of ios/ClarkePocket for ledger.v2.

Stdlib only. Reads files from git objects at a commit (never the working
tree), so the result depends only on the commit SHA.

Manifest (format IOS.POCKET.MANIFEST.v1)
  Every git-tracked blob under ios/ClarkePocket/ at <rev>, sorted by the
  UTF-8 bytes of its repo-relative path. One listing line per file:

      <sha256 hex> <size in bytes> <git mode> <path>\\n

  tree_root_sha256   = SHA-256 of the concatenated listing lines (UTF-8)
  tree_root_sha3_256 = SHA3-256 of the same bytes (ledger hash regime)
  git_tree           = `git rev-parse <rev>:ios/ClarkePocket` (cross-check)
  Gitlinks (submodules) are refused, not skipped.

Subcommands
  manifest     print the manifest as JSON
  plan         next ledger.v2 index, prev_hash, and whether the tree changed
  entry        write the next ledger.v2 entry (exclusive create, append-only)
  check-entry  re-derive an entry written by `entry` and compare

Ledger entry (ledger.v2/NNNN.yml, written by `entry`)
  Regime B seal, as verify_ledger.py computes for entry_index >= 9281:
      SHA3-256(GARDEN.EVENT.v1.LEDGER || 0x00 ||
               "<n>|<event>|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462")
  prev_hash = the declared digest of the current last entry
  (seal_sha3_256, else the seal tail, else terminal_hex), the same field
  verify_ledger.py entry_declared_digest() reads. The Regime B seal commits to
  index and event only; the body (per-file hashes) is committed by the
  ledger.v2 Merkle leaf (MERKLE.md: SHA3-256 over the canonical body).

Exit codes: 0 ok, 1 check mismatch, 2 usage/git error,
            3 index taken (collision), 4 tree unchanged since last iOS entry,
            5 CI evidence does not match the commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

FORMAT = "IOS.POCKET.MANIFEST.v1"
DEFAULT_PREFIX = "ios/ClarkePocket"
EVENT_PREFIX = "/ios_clarke_pocket_manifest_"
EVENT_DOMAIN_LEDGER = b"GARDEN.EVENT.v1.LEDGER"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"
REGIME_B_FROM = 9281
LOCAL_TZ = "America/New_York"
SIGN_OFF = "Clarke Yoursa Tee"

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX64_ANY = re.compile(r"[0-9a-fA-F]{64}")
ENTRY_FILE = re.compile(r"^(\d{4,6})\.ya?ml$")

EXIT_MISMATCH, EXIT_USAGE, EXIT_TAKEN, EXIT_UNCHANGED, EXIT_EVIDENCE = 1, 2, 3, 4, 5


class ManifestError(Exception):
    def __init__(self, msg: str, code: int = EXIT_USAGE):
        super().__init__(msg)
        self.code = code


# ── git ────────────────────────────────────────────────────────────────────
def _git(repo: Path, *args: str, data: Optional[bytes] = None) -> bytes:
    try:
        p = subprocess.run(["git", "-C", str(repo), *args], input=data,
                           capture_output=True, check=False)
    except FileNotFoundError as e:
        raise ManifestError(f"git not found: {e}")
    if p.returncode != 0:
        raise ManifestError(f"git {' '.join(args)} failed: "
                            f"{p.stderr.decode('utf-8', 'replace').strip()}")
    return p.stdout


def resolve_commit(repo: Path, rev: str) -> str:
    sha = _git(repo, "rev-parse", "--verify", "--end-of-options",
               f"{rev}^{{commit}}").decode().strip()
    if not HEX40.match(sha):
        raise ManifestError(f"rev {rev!r} did not resolve to a 40-hex commit: {sha!r}")
    return sha


# ── manifest ───────────────────────────────────────────────────────────────
def build_manifest(repo: Path, rev: str = "HEAD",
                   prefix: str = DEFAULT_PREFIX) -> Dict[str, Any]:
    prefix = prefix.strip("/")
    commit = resolve_commit(repo, rev)
    raw = _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit, "--", prefix + "/")
    rows = []
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, path_b = rec.split(b"\t", 1)
        mode, typ, oid = meta.decode().split(" ")
        path = path_b.decode("utf-8")
        if not path.startswith(prefix + "/"):
            continue
        if typ != "blob":
            raise ManifestError(f"{path}: git object type {typ} (mode {mode}) is not a blob; "
                                "gitlinks are not supported")
        rows.append((path_b, path, mode, oid))
    if not rows:
        raise ManifestError(f"no tracked files under {prefix}/ at {commit}")
    rows.sort(key=lambda r: r[0])

    batch = _git(repo, "cat-file", "--batch",
                 data=b"".join(r[3].encode() + b"\n" for r in rows))
    files: List[Dict[str, Any]] = []
    pos = 0
    for _path_b, path, mode, oid in rows:
        nl = batch.index(b"\n", pos)
        h_oid, h_typ, h_size = batch[pos:nl].decode().split(" ")
        if h_oid != oid or h_typ != "blob":
            raise ManifestError(f"git cat-file returned {h_oid} {h_typ} for {path} ({oid})")
        size = int(h_size)
        content = batch[nl + 1: nl + 1 + size]
        pos = nl + 1 + size + 1  # trailing LF after each object
        files.append({"path": path, "size": size, "mode": mode,
                      "sha256": hashlib.sha256(content).hexdigest()})

    listing = listing_bytes(files)
    git_tree = _git(repo, "rev-parse", f"{commit}:{prefix}").decode().strip()
    return {
        "format": FORMAT,
        "path": prefix + "/",
        "commit": commit,
        "git_tree": git_tree,
        "file_count": len(files),
        "total_bytes": sum(f["size"] for f in files),
        "tree_root_sha256": hashlib.sha256(listing).hexdigest(),
        "tree_root_sha3_256": hashlib.sha3_256(listing).hexdigest(),
        "files": files,
    }


def listing_bytes(files: Sequence[Dict[str, Any]]) -> bytes:
    return "".join(f"{f['sha256']} {f['size']} {f['mode']} {f['path']}\n"
                   for f in files).encode("utf-8")


# ── ledger reading (top-level scalars only; stdlib) ────────────────────────
def _top_scalars(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*?)[ \t]*$", line)
        if not m:
            continue
        v = m.group(2)
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        out.setdefault(m.group(1), v)
    return out


def declared_digest(scalars: Dict[str, str]) -> Optional[str]:
    """Mirror of verify_ledger.entry_declared_digest for top-level scalars."""
    s = scalars.get("seal_sha3_256", "").strip()
    if HEX64.match(s.lower()):
        return s.lower()
    hits = HEX64_ANY.findall(scalars.get("seal", ""))
    if hits:
        return hits[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = scalars.get(key, "").strip()
        if HEX64.match(v.lower()):
            return v.lower()
    return None


def read_ledger(ledger_dir: Path) -> List[Dict[str, Any]]:
    entries = []
    if not ledger_dir.is_dir():
        raise ManifestError(f"ledger dir not found: {ledger_dir}")
    for p in sorted(ledger_dir.iterdir()):
        m = ENTRY_FILE.match(p.name)
        if not m or not p.is_file():
            continue
        sc = _top_scalars(p.read_text(encoding="utf-8"))
        idx = sc.get("entry_index", "")
        if not idx.isdigit():
            continue
        entries.append({"index": int(idx), "file": p, "scalars": sc})
    return entries


def plan(repo: Path, ledger_dir: Path, manifest: Dict[str, Any],
         taken: Sequence[int] = (), flat_dir: Optional[Path] = None) -> Dict[str, Any]:
    entries = read_ledger(ledger_dir)
    if not entries:
        raise ManifestError(f"no entries in {ledger_dir}")
    by_index: Dict[int, List[Dict[str, Any]]] = {}
    for e in entries:
        by_index.setdefault(e["index"], []).append(e)
    dup = sorted(i for i, v in by_index.items() if len(v) > 1)
    if dup:
        raise ManifestError(f"duplicate entry_index in {ledger_dir}: {dup}")
    last = max(entries, key=lambda e: e["index"])
    if int(ENTRY_FILE.match(last["file"].name).group(1)) != last["index"]:
        raise ManifestError(f"{last['file']} holds entry_index {last['index']}; "
                            "filename and index disagree")
    prev_hash = declared_digest(last["scalars"])
    if not prev_hash:
        raise ManifestError(f"{last['file']} has no 64-hex declared digest; chain cannot form")
    nxt = last["index"] + 1

    clashes = []
    if nxt in set(int(t) for t in taken):
        clashes.append(f"index {nxt} is claimed by a pending ledger PR or branch")
    for ext in (".yml", ".yaml"):
        if (ledger_dir / f"{nxt}{ext}").exists():
            clashes.append(f"{ledger_dir / (str(nxt) + ext)} already exists")
        if flat_dir is not None and (flat_dir / f"{nxt}{ext}").exists():
            clashes.append(f"{flat_dir / (str(nxt) + ext)} exists in the flat root")
    if clashes:
        raise ManifestError("ledger.v2 index collision: " + "; ".join(clashes)
                            + ". Land or close the pending ledger PR, then re-run "
                            "(workflow_dispatch with head_sha).", EXIT_TAKEN)

    ios = [e for e in entries if "ios_pocket_tree_root" in e["scalars"]]
    prev_ios = max(ios, key=lambda e: e["index"]) if ios else None
    prev_root = prev_ios["scalars"]["ios_pocket_tree_root"].lower() if prev_ios else None
    return {
        "next_index": nxt,
        "prev_index": last["index"],
        "prev_file": last["file"].name,
        "prev_hash": prev_hash,
        "previous_ios_entry": prev_ios["index"] if prev_ios else None,
        "previous_tree_root": prev_root,
        "tree_root_sha256": manifest["tree_root_sha256"],
        "unchanged": prev_root == manifest["tree_root_sha256"],
        "measured_commit": manifest["commit"],
        "file_count": manifest["file_count"],
    }


# ── seals and time ─────────────────────────────────────────────────────────
def event_hash(n: int, event: str) -> str:
    if n < REGIME_B_FROM:
        raise ManifestError(f"entry_index {n} < {REGIME_B_FROM}: not a GARDEN.EVENT.v1.LEDGER index")
    payload = f"{n}|{event.strip()}|phi2={PHI2}|delta={DELTA}|theta={THETA}".encode("ascii")
    return hashlib.sha3_256(EVENT_DOMAIN_LEDGER + b"\x00" + payload).hexdigest()


def _tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(LOCAL_TZ)
    except Exception:  # no tzdata: still an explicit offset (+00:00)
        return timezone.utc


def iso_local(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ManifestError("naive datetime refused; timestamps need an explicit offset")
    return dt.astimezone(_tz()).isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as e:
        raise ManifestError(f"not ISO 8601: {value!r} ({e})")
    if dt.tzinfo is None:
        raise ManifestError(f"timestamp without offset refused: {value!r}")
    return dt


# ── YAML emitting (constrained subset, stdlib) ─────────────────────────────
def q(s: str) -> str:
    """Double-quoted YAML scalar (JSON string syntax is valid YAML)."""
    out = json.dumps(s, ensure_ascii=False)
    if not all(c.isprintable() for c in s):
        out = json.dumps(s, ensure_ascii=True)
    return out


def manifest_block(manifest: Dict[str, Any], indent: str = "    ") -> str:
    """The exact text of payload.ios_clarke_pocket's manifest fields.

    check-entry regenerates this block from the commit and requires it to
    appear verbatim in the entry.
    """
    lines = [
        f"{indent}format: {q(manifest['format'])}",
        f"{indent}path: {q(manifest['path'])}",
        f"{indent}commit: {q(manifest['commit'])}",
        f"{indent}git_tree: {q(manifest['git_tree'])}",
        f"{indent}file_count: {manifest['file_count']}",
        f"{indent}total_bytes: {manifest['total_bytes']}",
        f"{indent}tree_root_sha256: {q(manifest['tree_root_sha256'])}",
        f"{indent}tree_root_sha3_256: {q(manifest['tree_root_sha3_256'])}",
        f"{indent}files:",
    ]
    for f in manifest["files"]:
        lines.append(f"{indent}- {{path: {q(f['path'])}, size: {f['size']}, "
                     f"mode: {q(f['mode'])}, sha256: {q(f['sha256'])}}}")
    return "\n".join(lines) + "\n"


def render_entry(manifest: Dict[str, Any], pl: Dict[str, Any], ci: Dict[str, Any],
                 timestamp: str, ledger_main: str) -> str:
    n, commit = pl["next_index"], manifest["commit"]
    event = EVENT_PREFIX + commit
    h = event_hash(n, event)
    label = f"IOS_CLARKE_POCKET_MANIFEST_{n}"
    prev_ios = pl["previous_ios_entry"]
    note = (f"New append-only entry ({pl['prev_file']} and every other ledger file untouched). "
            f"Records sha256 and byte size of all {manifest['file_count']} git-tracked files under "
            f"{manifest['path']} at {commit}, read from git objects by tools/ios_pocket_manifest.py "
            f"({FORMAT}). Written only after the iOS Pocket Simulator workflow concluded success on "
            f"that exact commit (run {ci['run_id']}, read from the GitHub Actions API). "
            f"No claim beyond those bytes and that run. Signed-off-by: {SIGN_OFF}.")
    o = []
    a = o.append
    a(f"entry_index: {n}")
    a(f"event: {q(event)}")
    a("status: SEALED")
    a(f"timestamp: {q(timestamp)}")
    a("hash_algo: sha3_256")
    a(f"measured_at_commit: {q(commit)}")
    a(f"commander: {SIGN_OFF}")
    a(f"sign_off: {SIGN_OFF}")
    a("open_ended: true")
    a(f"even_index: {'true' if n % 2 == 0 else 'false'}")
    a(f"prev_hash: {q(pl['prev_hash'])}")
    a(f"witness_chain: {pl['prev_index']} -> {n}")
    a(f"note: {q(note)}")
    a(f"ios_pocket_tree_root: {q(manifest['tree_root_sha256'])}")
    a("payload:")
    a("  ios_clarke_pocket:")
    o.append(manifest_block(manifest).rstrip("\n"))
    a(f"    listing_rule: {q('<sha256> <size> <mode> <path> LF per file, sorted by UTF-8 path bytes; roots are SHA-256 and SHA3-256 of the listing')}")
    a(f"    tool: {q('tools/ios_pocket_manifest.py')}")
    a(f"    previous_ios_entry: {prev_ios if prev_ios is not None else q('none')}")
    a(f"    previous_tree_root: {q(pl['previous_tree_root'] or 'none')}")
    a("ci:")
    a(f"  measured_commit: {q(commit)}")
    a(f"  source: {q('GitHub Actions API actions/runs/' + str(ci['run_id']) + ', read ' + ci['read_at'])}")
    a("  ios_pocket_simulator:")
    a(f"    workflow: {q('iOS Pocket Simulator')}")
    a(f"    workflow_file: {q('.github/workflows/ios-pocket-simulator.yml')}")
    a(f"    run_id: {ci['run_id']}")
    a(f"    run_attempt: {ci['run_attempt']}")
    a(f"    run_url: {q(ci['run_url'])}")
    a(f"    event: {q(ci['event'])}")
    a(f"    head_branch: {q(ci['head_branch'])}")
    a(f"    head_sha: {q(ci['head_sha'])}")
    a(f"    status: {q(ci['status'])}")
    a(f"    conclusion: {q(ci['conclusion'])}")
    a(f"    completed_at: {q(ci['completed_at'])}")
    a(f"  policy: {q('NO-GHOST-PASS: only the run that exists on the measured commit is cited')}")
    a("chain:")
    a(f"  prev_entry: {pl['prev_index']}")
    a(f"  prev_hash: {q(pl['prev_hash'])}")
    a(f"  prev_hash_source: {q('ledger.v2/' + pl['prev_file'] + ' declared digest (seal_sha3_256) on main ' + ledger_main)}")
    a(f"  witness_chain: {pl['prev_index']} -> {n}")
    a(f"seal_preimage_rule: {q('Regime B (verify_ledger.py event_hash): SHA3-256(GARDEN.EVENT.v1.LEDGER || 0x00 || <entry_index>|<event>|phi2=' + PHI2 + '|delta=' + DELTA + '|theta=' + THETA + '), ASCII payload; the digest commits to entry_index and event only, the body is committed by the ledger.v2 Merkle leaf')}")
    a(f"regime_b_event_domain_sha3_256: {q(h)}")
    a("math_origin: |")
    a("  Event hash domain GARDEN.EVENT.v1.LEDGER || 0x00 ||")
    a(f"  {n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}")
    a(f"  SHA3-256 = {h}")
    a(f"terminal_hex: {q(h)}")
    a(f"seal: ∀∞φ² · {label} · WOOD_DRAGON_0.91 · SEALED · {h}")
    a(f"seal_sha3_256: {q(h)}")
    return "\n".join(o) + "\n"


def check_ci(ci: Dict[str, Any], commit: str) -> Dict[str, Any]:
    problems = []
    if ci.get("head_sha") != commit:
        problems.append(f"run head_sha {ci.get('head_sha')!r} != measured commit {commit}")
    if ci.get("status") != "completed" or ci.get("conclusion") != "success":
        problems.append(f"run status/conclusion {ci.get('status')}/{ci.get('conclusion')} is not completed/success")
    if ci.get("event") != "push" or ci.get("head_branch") != "main":
        problems.append(f"run event/branch {ci.get('event')}/{ci.get('head_branch')} is not push/main")
    if not str(ci.get("run_id", "")).isdigit():
        problems.append(f"run_id {ci.get('run_id')!r} is not numeric")
    if problems:
        raise ManifestError("CI evidence refused: " + "; ".join(problems), EXIT_EVIDENCE)
    out = dict(ci)
    out["completed_at"] = iso_local(parse_iso(ci["completed_at"]))
    return out


# ── check-entry ────────────────────────────────────────────────────────────
def check_entry(repo: Path, entry_path: Path, ledger_dir: Path) -> List[str]:
    text = entry_path.read_text(encoding="utf-8")
    sc = _top_scalars(text)
    problems: List[str] = []
    n = int(sc.get("entry_index", "-1")) if sc.get("entry_index", "").isdigit() else -1
    commit = sc.get("measured_at_commit", "")
    event = sc.get("event", "")
    if not HEX40.match(commit):
        return [f"measured_at_commit is not 40-hex: {commit!r}"]
    if event != EVENT_PREFIX + commit:
        problems.append(f"event {event!r} != {EVENT_PREFIX + commit!r}")
    if entry_path.name not in (f"{n}.yml", f"{n}.yaml"):
        problems.append(f"filename {entry_path.name} does not match entry_index {n}")
    m = build_manifest(repo, commit)
    if manifest_block(m) not in text:
        problems.append("payload manifest block differs from the manifest recomputed at "
                        f"{commit} (root {m['tree_root_sha256']})")
    if sc.get("ios_pocket_tree_root", "").lower() != m["tree_root_sha256"]:
        problems.append("ios_pocket_tree_root differs from the recomputed root")
    h = event_hash(n, event) if n >= REGIME_B_FROM else None
    for key in ("seal_sha3_256", "terminal_hex", "regime_b_event_domain_sha3_256"):
        if sc.get(key, "").lower() != h:
            problems.append(f"{key} {sc.get(key)!r} != Regime B event hash {h}")
    if not sc.get("seal", "").endswith(f"· {h}"):
        problems.append("seal tail is not the Regime B event hash")
    prev = [e for e in read_ledger(ledger_dir) if e["index"] == n - 1]
    if len(prev) != 1:
        problems.append(f"predecessor {n - 1} not found exactly once in {ledger_dir}")
    else:
        want = declared_digest(prev[0]["scalars"])
        if sc.get("prev_hash", "").lower() != want:
            problems.append(f"prev_hash {sc.get('prev_hash')!r} != declared digest of {n - 1} ({want})")
    if sc.get("witness_chain", "") != f"{n - 1} -> {n}":
        problems.append(f"witness_chain {sc.get('witness_chain')!r} != '{n - 1} -> {n}'")
    ts = sc.get("timestamp", "")
    try:
        parse_iso(ts)
    except ManifestError as e:
        problems.append(str(e))
    return problems


# ── CLI ────────────────────────────────────────────────────────────────────
def _ci_from_args(a: argparse.Namespace) -> Dict[str, Any]:
    if a.ios_run_json:
        raw = json.loads(Path(a.ios_run_json).read_text(encoding="utf-8"))
        return {"run_id": raw.get("id"), "run_attempt": raw.get("run_attempt"),
                "run_url": raw.get("html_url"), "event": raw.get("event"),
                "head_branch": raw.get("head_branch"), "head_sha": raw.get("head_sha"),
                "status": raw.get("status"), "conclusion": raw.get("conclusion"),
                "completed_at": raw.get("updated_at"),
                "workflow_path": raw.get("path")}
    raise ManifestError("--ios-run-json is required (GitHub API actions/runs/<id> response)")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--repo", default=".", type=Path)
        p.add_argument("--prefix", default=DEFAULT_PREFIX)

    p = sub.add_parser("manifest"); common(p)
    p.add_argument("--rev", default="HEAD")
    p.add_argument("--listing", action="store_true", help="print the listing bytes instead of JSON")

    for name in ("plan", "entry"):
        p = sub.add_parser(name); common(p)
        p.add_argument("--rev", required=True)
        p.add_argument("--ledger-dir", default=None, type=Path)
        p.add_argument("--taken", type=int, action="append", default=[],
                       help="entry index already claimed by a pending PR/branch (repeatable)")
        if name == "entry":
            p.add_argument("--ios-run-json", required=True)
            p.add_argument("--ledger-main", required=True, help="40-hex main commit the entry is appended on")
            p.add_argument("--timestamp", default=None, help="ISO 8601 with offset (default: now)")
            p.add_argument("--read-at", default=None, help="when the CI run was read (default: timestamp)")
            p.add_argument("--out", default=None, type=Path, help="default: <ledger-dir>/<n>.yml")

    p = sub.add_parser("check-entry"); common(p)
    p.add_argument("entry", type=Path)
    p.add_argument("--ledger-dir", default=None, type=Path)

    a = ap.parse_args(argv)
    repo = a.repo.resolve()
    try:
        if a.cmd == "manifest":
            m = build_manifest(repo, a.rev, a.prefix)
            if a.listing:
                sys.stdout.buffer.write(listing_bytes(m["files"]))
            else:
                print(json.dumps(m, indent=2, ensure_ascii=False))
            return 0
        ledger_dir = (a.ledger_dir or repo / "ledger.v2")
        if a.cmd == "check-entry":
            probs = check_entry(repo, a.entry, ledger_dir)
            for pr in probs:
                print(f"❌ {a.entry}: {pr}")
            if not probs:
                print(f"✅ {a.entry}: manifest, root, seal, prev_hash and witness_chain re-derived")
            return EXIT_MISMATCH if probs else 0
        m = build_manifest(repo, a.rev, a.prefix)
        pl = plan(repo, ledger_dir, m, a.taken, flat_dir=repo / "ledger")
        if a.cmd == "plan":
            print(json.dumps(pl, indent=2))
            return 0
        if pl["unchanged"]:
            raise ManifestError(f"{m['path']} tree root {m['tree_root_sha256']} equals entry "
                                f"{pl['previous_ios_entry']}; nothing to record", EXIT_UNCHANGED)
        if not HEX40.match(a.ledger_main):
            raise ManifestError(f"--ledger-main must be 40-hex, got {a.ledger_main!r}")
        ci = _ci_from_args(a)
        if ci.get("workflow_path") not in (None, ".github/workflows/ios-pocket-simulator.yml"):
            raise ManifestError(f"run is from {ci['workflow_path']}, not ios-pocket-simulator.yml",
                                EXIT_EVIDENCE)
        ts = iso_local(parse_iso(a.timestamp)) if a.timestamp else iso_local(datetime.now(timezone.utc))
        ci["read_at"] = iso_local(parse_iso(a.read_at)) if a.read_at else ts
        ci = check_ci(ci, m["commit"])
        text = render_entry(m, pl, ci, ts, a.ledger_main)
        out = a.out or ledger_dir / f"{pl['next_index']}.yml"
        try:
            with open(out, "x", encoding="utf-8") as fh:  # append-only: never overwrite
                fh.write(text)
        except FileExistsError:
            raise ManifestError(f"{out} exists — append-only, refusing to overwrite", EXIT_TAKEN)
        print(json.dumps({"written": str(out), **pl}, indent=2))
        return 0
    except ManifestError as e:
        print(f"::error::{e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    raise SystemExit(main())
