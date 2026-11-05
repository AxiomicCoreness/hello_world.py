#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""ledger_index.py — read ledger/ and ledger.v2/ in unison. Read-only on both folders.

  python tools/ledger_index.py            # write ledger_index.jsonl, append ledger.chain.jsonl
  python tools/ledger_index.py --check    # fail (exit 1) if either is stale or the chain breaks

Unified schema per row (docs/ledger-unison.md):
  entry_index, folder, path, doc, event, timestamp (ISO-8601 UTC or null),
  status, commander, null_ban, witness_chain, seal, seal_status, seal_regimes,
  flags[], raw{original fields}
Never fails open: a file that can't be read or parsed becomes a flagged row.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger_seal  # noqa: E402

try:
    import yaml
except ImportError:  # never fail open
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

FOLDERS = ("ledger", "ledger.v2")
YAML_SUFFIXES = (".yaml", ".yml")
INDEX_FILE = "ledger_index.jsonl"
CHAIN_FILE = "ledger.chain.jsonl"
GENESIS = "0" * 64
OUTLIER_MAX = 99999  # main sequence is 0..9xxx; 510510 series is flagged

# old field name -> unified name (first present wins, in this order)
ALIASES = {
    "null_ban": ("null_ban", "nullify_ban", "null_ban_sigma", "nullban"),
    "timestamp": ("timestamp", "timestamp_utc", "ts", "time", "date", "sealed_at", "created"),
    "commander": ("commander", "operator", "author"),
    "status": ("status", "state"),
    "event": ("event", "event_type", "name"),
}
ISO_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}:\d{2}(?::\d{2})?)(?:\.\d+)?)?\s*(Z|[+-]\d{2}:?\d{2})?")


def norm_timestamp(v: Any) -> Optional[str]:
    if isinstance(v, _dt.datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=_dt.timezone.utc)
        return v.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(v, _dt.date):
        return v.isoformat() + "T00:00:00Z"
    if isinstance(v, (int, float)) and not isinstance(v, bool) and 1e9 < v < 1e10:
        return _dt.datetime.fromtimestamp(v, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(v, str):
        m = ISO_RE.search(v)
        if not m:
            return None
        date, tm, tz = m.group(1), m.group(2) or "00:00:00", m.group(3) or "Z"
        if len(tm) == 5:
            tm += ":00"
        try:
            d = _dt.datetime.fromisoformat(f"{date}T{tm}" + ("+00:00" if tz == "Z" else tz[:3] + ":" + tz[-2:]))
        except ValueError:
            return None
        return d.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def _strkeys(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _strkeys(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_strkeys(v) for v in o]
    return o


def _jsonable(o: Any) -> Any:
    return json.loads(json.dumps(_strkeys(o), default=ledger_seal.json_default, ensure_ascii=False))


def _as_int(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def list_files(root: Path) -> List[Path]:
    out = []
    for f in FOLDERS:
        d = root / f
        if d.is_dir():
            out += [p for p in d.iterdir() if p.is_file() and p.suffix in YAML_SUFFIXES]
    return out


def read_file(root: Path, p: Path) -> List[Dict[str, Any]]:
    rel = p.relative_to(root).as_posix()
    folder = rel.split("/", 1)[0]
    stem_idx = _as_int(p.stem)
    base = {"folder": folder, "path": rel}
    try:
        docs = [d for d in yaml.safe_load_all(p.read_text(encoding="utf-8")) if d is not None]
    except Exception as e:  # noqa: BLE001 — flagged, never dropped
        return [dict(base, doc=0, entry_index=stem_idx, seal_status=ledger_seal.UNVERIFIED,
                     seal_regimes=[], flags=["parse_error"], error=f"{type(e).__name__}: {str(e)[:200]}",
                     raw=None)]
    rows = []
    if not docs:
        return [dict(base, doc=0, entry_index=stem_idx, seal_status=ledger_seal.NO_SEAL,
                     seal_regimes=[], flags=["empty_file"], raw=None)]
    for i, d in enumerate(docs):
        flags: List[str] = []
        if not isinstance(d, dict):
            rows.append(dict(base, doc=i, entry_index=stem_idx, seal_status=ledger_seal.UNVERIFIED,
                             seal_regimes=[], flags=["non_mapping_document"], raw=_jsonable(d)))
            continue
        n = _as_int(d.get("entry_index"))
        if n is None:
            flags.append("missing_entry_index")
            n = stem_idx
        elif stem_idx is not None and n != stem_idx:
            flags.append("index_filename_mismatch")
        row: Dict[str, Any] = dict(base, doc=i, entry_index=n)
        for uni, names in ALIASES.items():
            hit = [k for k in names if k in d]
            row[uni] = d[hit[0]] if hit else None
            if hit and hit[0] != uni:
                row.setdefault("field_aliases", {})[uni] = hit[0]
        raw_ts = row["timestamp"]
        row["timestamp"] = norm_timestamp(raw_ts)
        if raw_ts is not None and row["timestamp"] is None:
            flags.append("timestamp_unparsed")
        row["witness_chain"] = d.get("witness_chain")
        row["seal"] = d.get("seal")
        v = ledger_seal.verify_entry(d, n)
        row["seal_status"] = v["status"]
        row["seal_regimes"] = v["regimes"]
        if v.get("reason"):
            flags.append("seal_sha3_256_mismatch")
        if v["regime_mismatch"]:
            flags.append("seal_method_mismatch")
        if v["status"] == ledger_seal.UNVERIFIED:
            flags.append("seal_unverified")
        if n is not None and (n < 0 or n > OUTLIER_MAX):
            flags.append("outlier_index")
        row["flags"] = flags
        row["raw"] = _jsonable(d)
        rows.append({k: _jsonable(v2) if k in ("event", "status", "commander", "null_ban", "witness_chain", "seal") else v2
                     for k, v2 in row.items()})
    return rows


def sort_key(r: Dict[str, Any]) -> Tuple:
    n = r.get("entry_index")
    return (0 if isinstance(n, int) else 1, n if isinstance(n, int) else 0, r["folder"], r["path"], r["doc"])


def build_index(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p in list_files(root):
        rows += read_file(root, p)
    rows.sort(key=sort_key)
    seen: Dict[int, List[Dict[str, Any]]] = {}
    for r in rows:
        if isinstance(r.get("entry_index"), int):
            seen.setdefault(r["entry_index"], []).append(r)
    for n, group in seen.items():
        if len(group) > 1:
            folders = {g["folder"] for g in group}
            tag = "duplicate_index_cross_folder" if len(folders) > 1 and all(
                sum(1 for g in group if g["folder"] == f) == 1 for f in folders) else "duplicate_index"
            for g in group:
                g["flags"].append(tag)
    return rows


def file_sha256(root: Path, rel: str) -> str:
    return hashlib.sha256((root / rel).read_bytes()).hexdigest()


def _file_order(root: Path) -> List[Tuple[Optional[int], str]]:
    keyed = {}
    for p in list_files(root):
        rel = p.relative_to(root).as_posix()
        keyed[rel] = _as_int(p.stem)
    return sorted(((n, rel) for rel, n in keyed.items()),
                  key=lambda t: (0 if t[0] is not None else 1, t[0] or 0, t[1].split("/")[0], t[1]))


def load_chain(root: Path) -> List[Dict[str, Any]]:
    f = root / CHAIN_FILE
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def check_chain(root: Path, chain: List[Dict[str, Any]]) -> List[str]:
    errs = []
    prev = GENESIS
    seen = set()
    for i, c in enumerate(chain):
        if c.get("seq") != i:
            errs.append(f"line {i}: seq {c.get('seq')} != {i}")
        if c.get("prev_hash") != prev:
            errs.append(f"line {i} ({c.get('path')}): prev_hash breaks chain")
        p = root / c.get("path", "")
        if not p.is_file():
            errs.append(f"line {i}: {c.get('path')} missing (ledger is append-only)")
        elif file_sha256(root, c["path"]) != c.get("sha256"):
            errs.append(f"line {i}: {c['path']} bytes changed (ledger is append-only)")
        if c.get("path") in seen:
            errs.append(f"line {i}: {c.get('path')} repeated")
        seen.add(c.get("path"))
        prev = c.get("sha256")
    return errs


def extend_chain(root: Path, chain: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    have = {c["path"] for c in chain}
    out = list(chain)
    prev = out[-1]["sha256"] if out else GENESIS
    for n, rel in _file_order(root):
        if rel in have:
            continue
        h = file_sha256(root, rel)
        out.append({"seq": len(out), "entry_index": n, "path": rel, "sha256": h, "prev_hash": prev})
        prev = h
    return out


def dump_jsonl(rows: List[Dict[str, Any]]) -> str:
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    s: Dict[str, Any] = {"rows": len(rows), "files": len({r["path"] for r in rows}), "seal_status": {}, "flags": {}}
    for r in rows:
        s["seal_status"][r["seal_status"]] = s["seal_status"].get(r["seal_status"], 0) + 1
        for f in r["flags"]:
            s["flags"][f] = s["flags"].get(f, 0) + 1
    s["flagged_rows"] = sum(1 for r in rows if r["flags"])
    return s


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true", help="verify committed index/chain are current")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    t0 = time.perf_counter()
    rows = build_index(root)
    if not rows:
        print("ERROR: no ledger files found", file=sys.stderr)
        return 2
    text = dump_jsonl(rows)
    chain = load_chain(root)
    errs = check_chain(root, chain)
    new_chain = extend_chain(root, chain) if not errs else chain
    dt = (time.perf_counter() - t0) * 1000
    s = summarize(rows)
    s["read_ms"] = round(dt, 1)
    print(json.dumps(s, sort_keys=True))
    if errs:
        for e in errs:
            print(f"::error::chain: {e}")
        return 1
    if a.check:
        bad = 0
        idx = root / INDEX_FILE
        if not idx.exists() or idx.read_text(encoding="utf-8") != text:
            print(f"::error::{INDEX_FILE} is stale; run python tools/ledger_index.py and commit")
            bad = 1
        if len(new_chain) != len(chain):
            print(f"::error::{CHAIN_FILE} is stale ({len(new_chain) - len(chain)} files unchained); "
                  "run python tools/ledger_index.py and commit")
            bad = 1
        if not bad:
            print(f"OK: index current, chain unbroken ({len(chain)} links)")
        return bad
    (root / INDEX_FILE).write_text(text, encoding="utf-8")
    with open(root / CHAIN_FILE, "a", encoding="utf-8") as f:  # append-only
        f.write(dump_jsonl(new_chain[len(chain):]))
    print(f"wrote {INDEX_FILE} ({len(rows)} rows), appended {len(new_chain) - len(chain)} chain links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
