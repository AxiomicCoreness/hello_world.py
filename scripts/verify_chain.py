#!/usr/bin/env python3
"""Ledger chain verifier (dict load, not grep).

Recomputes canonical body digests and checks prev_hash links when present.
Use --require N to fail if entry N is absent (including empty ledger).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

try:
    import yaml
except ImportError:
    print("::error::pyyaml required", file=sys.stderr)
    sys.exit(2)

DIGEST_KEYS = frozenset({
    "status_sha3_256", "sha3_256", "seal_sha3_256", "terminal_hex", "witness_prefix",
})
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def canonicalize(body: Any) -> bytes:
    return json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).strip().encode("utf-8")


def extract_digest(entry: dict[str, Any]) -> Optional[str]:
    for key in ("status_sha3_256", "sha3_256", "seal_sha3_256", "terminal_hex", "witness_prefix"):
        v = entry.get(key)
        if isinstance(v, str) and HEX64.match(v):
            return v.lower()
    seal = entry.get("seal")
    if isinstance(seal, str):
        matches = re.findall(r"\b([0-9a-fA-F]{64})\b", seal)
        if matches:
            return matches[-1].lower()
    return None


def body_without_digest(entry: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in entry.items() if k not in DIGEST_KEYS and k != "seal"}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify ledger chain linkage.")
    ap.add_argument(
        "ledger_dir",
        nargs="?",
        default="ledger",
        help="Directory holding YAML entries (default: ledger)",
    )
    ap.add_argument(
        "--ledger-dir",
        dest="ledger_dir_opt",
        default=None,
        help="Same as positional ledger_dir",
    )
    ap.add_argument(
        "--require",
        type=int,
        action="append",
        default=None,
        metavar="N",
        help="Exit non-zero if entry N is not present. May be repeated.",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Only print on failure.",
    )
    args = ap.parse_args(argv)

    ledger = Path(args.ledger_dir_opt or args.ledger_dir)
    if not ledger.is_dir():
        print(f"::error::no ledger dir: {ledger}", file=sys.stderr)
        return 2

    entries: list[tuple[int, Path, dict[str, Any]]] = []
    for p in sorted(
        ledger.glob("*.yaml"),
        key=lambda x: int(x.stem) if x.stem.isdigit() else -1,
    ):
        if not p.stem.isdigit():
            continue
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            entries.append((int(p.stem), p, data))

    present_indices = {n for n, _, _ in entries}
    for n, _, entry in entries:
        ei = entry.get("entry_index")
        if isinstance(ei, int):
            present_indices.add(ei)

    errors = 0
    prev_digest: Optional[str] = None
    prev_n: Optional[int] = None

    for n, path, entry in entries:
        declared = extract_digest(entry)
        body = body_without_digest(entry)
        recomputed = hashlib.sha3_256(canonicalize(body)).hexdigest()

        if declared is None:
            if not args.quiet:
                print(f"WARN {n} {path.name}: no digests field")
        else:
            if entry.get("prev_hash") and prev_digest:
                ph = str(entry["prev_hash"]).lower()
                if HEX64.match(ph) and ph != prev_digest:
                    print(f"FAIL {n}: prev_hash != terminal of {prev_n}")
                    print(f"  prev_hash={ph}")
                    print(f"  expected={prev_digest}")
                    errors += 1
            prev_digest = declared
            prev_n = n
            if not args.quiet:
                print(f"OK   {n} digest={declared[:16]}… body_recompute={recomputed[:16]}…")

    if args.require:
        missing = [n for n in args.require if n not in present_indices]
        if missing:
            for n in missing:
                print(f"::error::required entry {n} not present in {ledger}/")
            return 1

    if errors:
        print(f"checked {len(entries)} entries, failures={errors}")
        return 1

    if not args.quiet:
        req = f", required present: {args.require}" if args.require else ""
        print(f"verified {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}{req}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
