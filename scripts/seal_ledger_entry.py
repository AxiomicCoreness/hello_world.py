#!/usr/bin/env python3
"""Create next ledger entry from previous terminal digest. No fabricated hex."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("::error::pyyaml required", file=sys.stderr)
    sys.exit(2)

LEDGER_DIR = Path("ledger")
DIGEST_FIELD = "status_sha3_256"
HEX64 = re.compile(r"\b([0-9a-fA-F]{64})\b")


def canonicalize(body: Any) -> bytes:
    s = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.strip().encode("utf-8")


def extract_seal_hex(entry: dict[str, Any]) -> str:
    for key in (DIGEST_FIELD, "sha3_256", "seal_sha3_256", "terminal_hex", "witness_prefix"):
        v = entry.get(key)
        if isinstance(v, str) and re.fullmatch(r"[0-9a-fA-F]{64}", v):
            return v.lower()
    seal = entry.get("seal")
    if isinstance(seal, str):
        matches = HEX64.findall(seal)
        if matches:
            return matches[-1].lower()
    raise ValueError(f"no 64-hex digest in {DIGEST_FIELD!r} or seal")


def load_entry(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level is not a mapping")
    return data


def find_previous(n: int, ledger: Path) -> tuple[int, Path, dict[str, Any]]:
    candidates: list[tuple[int, Path]] = []
    for p in ledger.glob("*.yaml"):
        if p.stem.isdigit():
            k = int(p.stem)
            if k < n:
                candidates.append((k, p))
    if not candidates:
        raise FileNotFoundError(f"no ledger entry below {n}")
    k, p = max(candidates, key=lambda t: t[0])
    return k, p, load_entry(p)


def atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=True, default_flow_style=False, allow_unicode=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=int)
    parser.add_argument("--event", required=True)
    parser.add_argument("--fields", type=str, default="{}")
    parser.add_argument("--ledger", type=Path, default=LEDGER_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    target = args.ledger / f"{args.entry}.yaml"
    if target.exists() and not args.force:
        print(f"refusing to overwrite {target}; use --force", file=sys.stderr)
        return 1
    try:
        extra = json.loads(args.fields)
    except json.JSONDecodeError as e:
        print(f"--fields not JSON: {e}", file=sys.stderr)
        return 1
    if not isinstance(extra, dict):
        print("--fields must be object", file=sys.stderr)
        return 1

    try:
        prev_n, prev_path, prev_entry = find_previous(args.entry, args.ledger)
        prev_hex = extract_seal_hex(prev_entry)
    except (FileNotFoundError, ValueError) as e:
        print(f"cannot resolve previous entry: {e}", file=sys.stderr)
        return 2

    body: dict[str, Any] = {
        "entry_index": args.entry,
        "event": args.event,
        "prev_hash": prev_hex,
        "witness": f"{prev_n} → {args.entry} — UNBROKEN",
    }
    body.update(extra)
    digest = hashlib.sha3_256(canonicalize(body)).hexdigest()
    entry = dict(body)
    entry[DIGEST_FIELD] = digest

    if args.dry_run:
        print("prev:", prev_n, prev_path, prev_hex)
        print("canonical:", canonicalize(body).decode("utf-8"))
        print("digest:", digest)
        return 0

    atomic_write_yaml(target, entry)
    print(json.dumps({
        "written": str(target),
        "entry": args.entry,
        "prev_entry": prev_n,
        "prev_hash": prev_hex,
        "digest": digest,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
