#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Append one wood-dragon dispatch ledger entry. Never rewrite an existing file.

Index rule (same idea as tools/ios_pocket_manifest.py and the docstring on
scripts/ledger_append_canonical.py ``resolve_index``):

* If the preferred index (DISPATCH_ENTRY, default 9007) is free in both
  ``ledger/`` and ``ledger.v2/``, write that index.
* If it is already taken, do not open it for write. Append at the next free
  index at or above ``max(main-sequence)+1``. The main sequence is every
  numeric stem in either ledger folder with ``0 <= index <= 99999`` (the
  outlier ceiling in tools/ledger_index.py). The 510510 series is not a head,
  and historical gaps (for example 9010) stay empty.
* The new path is ``<ledger-dir>/<index>.yaml``, published with ``os.link``
  so a name that already exists is never replaced.
* ``prev_hash`` is the previous entry's declared seal digest (greatest index
  strictly below the new one, either folder). ``witness`` names that hop.
* Indexes >= 9281 are sealed with Regime B. Lower indexes use Regime A.
  Both are the digests ``tools/ledger_seal.py`` verifies.

This script does not touch ``ledger.chain.jsonl`` or ``ledger_index.jsonl``.
The workflow runs ``tools/ledger_index.py`` afterwards so the chain link is
appended by that tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import ledger_seal  # noqa: E402

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

OUTLIER_MAX = 99999
YAML_SUFFIXES = (".yaml", ".yml")


def numeric_entries(directory: Path) -> Dict[int, Path]:
    found: Dict[int, Path] = {}
    if not directory.is_dir():
        return found
    for path in directory.iterdir():
        if not path.is_file() and not path.is_symlink():
            continue
        if path.suffix not in YAML_SUFFIXES or not path.stem.isdigit():
            continue
        idx = int(path.stem)
        current = found.get(idx)
        if current is None or (current.is_symlink() and not path.is_symlink()):
            found[idx] = path
    return found


def collect_occupied(*dirs: Path) -> Dict[int, Path]:
    occupied: Dict[int, Path] = {}
    for directory in dirs:
        for idx, path in numeric_entries(directory).items():
            current = occupied.get(idx)
            if current is None or (current.is_symlink() and not path.is_symlink()):
                occupied[idx] = path
    return occupied


def choose_index(preferred: int, occupied: Dict[int, Path]) -> int:
    """Return preferred when it is free; otherwise the next free slot after the head."""
    if preferred < 0:
        raise SystemExit("preferred index must be >= 0")
    if preferred not in occupied:
        return preferred
    if preferred > OUTLIER_MAX:
        start = preferred + 1
    else:
        main = [n for n in occupied if 0 <= n <= OUTLIER_MAX]
        start = (max(main) + 1) if main else (preferred + 1)
    idx = start
    limit = max(start, preferred) + 100000
    while idx in occupied:
        idx += 1
        if idx > limit:
            raise SystemExit("no free ledger index at or above {0}".format(start))
    return idx


def declared_prev_hash(doc: object) -> str:
    if not isinstance(doc, dict):
        return ""
    digest = ledger_seal.declared_hex(doc)
    if digest:
        return digest
    explicit = doc.get("seal_sha3_256")
    if isinstance(explicit, str) and ledger_seal.HASH_RE.fullmatch(explicit.strip()):
        return explicit.strip().lower()
    seal = doc.get("seal")
    if isinstance(seal, str) and "·" in seal:
        return seal.rsplit("·", 1)[-1].strip()
    return ""


def load_regular(path: Path) -> Optional[dict]:
    if path.is_symlink() or not path.is_file():
        return None
    resolved = path.resolve()
    try:
        resolved.relative_to(path.parent.resolve())
    except ValueError:
        return None
    with path.open("r", encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    if not isinstance(doc, dict):
        return None
    return doc


def previous_of(idx: int, occupied: Dict[int, Path]) -> Optional[Tuple[int, Path]]:
    lower = [n for n in occupied if n < idx]
    if not lower:
        return None
    prev = max(lower)
    return prev, occupied[prev]


def terminals_digest(raw: str, algo: str) -> str:
    try:
        terminals = json.loads(raw) if raw else []
    except json.JSONDecodeError:
        terminals = []
    if not isinstance(terminals, list):
        terminals = []
    canon = json.dumps(terminals, sort_keys=True, separators=(",", ":"))
    return hashlib.new(algo, canon.encode("utf-8")).hexdigest()


def render_entry(doc: dict) -> str:
    """Dump YAML whose reloaded seal matches Regime A or B."""
    idx = doc["entry_index"]
    body = {k: v for k, v in doc.items() if k != "seal"}
    loaded = yaml.safe_load(
        yaml.safe_dump(body, sort_keys=False, allow_unicode=True, default_flow_style=False)
    )
    if not isinstance(loaded, dict):
        raise SystemExit("entry round-trip did not produce a mapping")
    if isinstance(idx, int) and idx >= ledger_seal.REGIME_B_FROM:
        digest = ledger_seal.regime_b(loaded, idx)
        if not digest:
            raise SystemExit("Regime B digest unavailable; event must be ASCII")
    else:
        digest = ledger_seal.regime_a(loaded)
    loaded["seal"] = (
        "∀∞φ² · WOOD_DRAGON_DISPATCH_{0} · WOOD_DRAGON_0.91 · SEALED · {1}".format(
            idx, digest
        )
    )
    text = yaml.safe_dump(
        loaded, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    again = yaml.safe_load(text)
    if isinstance(idx, int) and idx >= ledger_seal.REGIME_B_FROM:
        check = ledger_seal.regime_b(again, idx)
    else:
        check = ledger_seal.regime_a(again)
    if check != digest or ledger_seal.declared_hex(again) != digest:
        raise SystemExit("seal did not survive YAML dump")
    return text


def exclusive_write(path: Path, text: str) -> None:
    """Publish ``path`` only if that name does not already exist."""
    if os.path.lexists(path):
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".append-", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        if os.path.lexists(path):
            raise FileExistsError(path)
        os.link(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def append_dispatch(
    ledger_dir: Path,
    preferred: int,
    *,
    event: str,
    terminal_count: int,
    last_observed: int,
    i_of_144: str,
    mcp_contract_ok: str,
    mcp_url: str,
    mcp_port: str,
    mcp_namespace: str,
    terminals_json: str,
    hash_algo: str,
    also_dir: Optional[Path] = None,
) -> dict:
    ledger_dir = Path(ledger_dir)
    dirs = [ledger_dir]
    if also_dir is not None:
        dirs.append(Path(also_dir))
    occupied = collect_occupied(*dirs)
    idx = choose_index(preferred, occupied)
    dest = ledger_dir / "{0}.yaml".format(idx)
    if os.path.lexists(dest) or idx in occupied:
        raise FileExistsError("refusing to modify existing ledger index {0}".format(idx))
    prev = previous_of(idx, occupied)
    if prev is None:
        prev_index = None
        prev_hash = ""
        witness = "GENESIS → {0} — UNBROKEN".format(idx)
    else:
        prev_index, prev_path = prev
        prev_hash = declared_prev_hash(load_regular(prev_path) or {})
        witness = "{0} → {1} — UNBROKEN".format(prev_index, idx)
    mcp_set = bool(mcp_url)
    mcp_ok = str(mcp_contract_ok).lower() == "true"
    entry = {
        "entry_index": idx,
        "event": event,
        "status": "SUCCESS" if mcp_ok or not mcp_set else "DEGRADED",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": hash_algo,
        "observation_channel": "wood_dragon_dispatch",
        "dispatcher": "quantum.wood_dragon_dispatch",
        "terminal_count": int(terminal_count),
        "last_observed_count": int(last_observed),
        "terminals_sha3_256": terminals_digest(terminals_json, hash_algo),
        "i_of_144": str(i_of_144),
        "grava_star_fired": False,
        "mcp_pulse": "sent" if mcp_set else "skipped",
        "mcp_contract_ok": mcp_ok,
        "mcp_port": str(mcp_port),
        "mcp_namespace": str(mcp_namespace),
        "prev_hash": prev_hash,
        "witness": witness,
    }
    exclusive_write(dest, render_entry(entry))
    return {
        "entry_index": idx,
        "path": dest,
        "preferred": preferred,
        "prev_index": prev_index,
        "prev_hash": prev_hash,
        "witness": witness,
        "appended": idx != preferred,
    }


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _write_github_output(result: dict, rel: str) -> None:
    destination = os.environ.get("GITHUB_OUTPUT")
    if not destination:
        return
    with open(destination, "a", encoding="utf-8") as handle:
        handle.write("entry_index={0}\n".format(result["entry_index"]))
        handle.write("entry_file={0}\n".format(rel))
        handle.write("prev_hash={0}\n".format(result["prev_hash"]))
        handle.write("witness={0}\n".format(result["witness"]))


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger-dir", default=os.environ.get("LEDGER_DIR", "ledger"))
    parser.add_argument("--also-dir", default=None)
    parser.add_argument(
        "--preferred",
        type=int,
        default=int(os.environ.get("DISPATCH_ENTRY", "9007")),
    )
    parser.add_argument(
        "--event",
        default=os.environ.get("EVENT_PATH", "/workflow_dispatch_wood_dragon_mistral"),
    )
    parser.add_argument(
        "--terminal-count",
        type=int,
        default=int(os.environ.get("TERMINAL_COUNT", "0")),
    )
    parser.add_argument(
        "--last-observed",
        type=int,
        default=int(os.environ.get("LAST_OBSERVED", "26")),
    )
    parser.add_argument("--i-of-144", default=os.environ.get("I_OF_144", "1"))
    parser.add_argument(
        "--mcp-contract-ok",
        default=os.environ.get("MCP_CONTRACT_OK", "false"),
    )
    parser.add_argument("--mcp-url", default=os.environ.get("MCP_CONNECTOR_URL", ""))
    parser.add_argument("--mcp-port", default=os.environ.get("MCP_PORT", "13800"))
    parser.add_argument(
        "--mcp-namespace",
        default=os.environ.get("MCP_NAMESPACE", "wood-dragon-dispatch"),
    )
    parser.add_argument(
        "--terminals-json",
        default=os.environ.get("TERMINALS_JSON", "[]"),
    )
    parser.add_argument("--hash-algo", default=os.environ.get("HASH_ALGO", "sha3_256"))
    args = parser.parse_args(argv)
    ledger_dir = Path(args.ledger_dir)
    also = Path(args.also_dir) if args.also_dir else None
    if also is None:
        sibling = ledger_dir.parent / "ledger.v2"
        if ledger_dir.name == "ledger" and sibling.is_dir():
            also = sibling
    try:
        result = append_dispatch(
            ledger_dir,
            args.preferred,
            event=args.event,
            terminal_count=args.terminal_count,
            last_observed=args.last_observed,
            i_of_144=args.i_of_144,
            mcp_contract_ok=args.mcp_contract_ok,
            mcp_url=args.mcp_url,
            mcp_port=args.mcp_port,
            mcp_namespace=args.mcp_namespace,
            terminals_json=args.terminals_json,
            hash_algo=args.hash_algo,
            also_dir=also,
        )
    except FileExistsError as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        return 1
    rel = _rel(result["path"])
    _write_github_output(result, rel)
    action = "appended" if result["appended"] else "created"
    print("{0} ledger entry {1} at {2}".format(action, result["entry_index"], rel))
    print("witness: {0}".format(result["witness"]))
    print("prev_hash: {0}".format(result["prev_hash"] or "(none)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
