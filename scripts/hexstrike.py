#!/usr/bin/env python3
"""
hexstrike.py — ghost-seal scanner for append-only ledger entries.

Defect class: ghost_seal

Subtypes (byte-level):
  forged_seal              declared seal != recomputed seal over payload
  empty_payload            seal asserted, payload absent
  no_evidence              seal present, evidence_at_seal_time empty list
  unsealed_with_evidence   evidence present, seal is null/absent

Pure stdlib. Optional PyYAML if installed; otherwise JSON-only parse.
Exit: 0 clean, 1 findings, 2 usage/IO.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

CATALOGUED_CLASS = "ghost_seal"
SEAL_ALGORITHM = "sha3-256"


def compute_seal(payload: dict) -> str:
    """sha3_256(json.dumps(payload, sort_keys=True)) — default separators."""
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha3_256(raw).hexdigest()


class Kind:
    FORGED = "forged_seal"
    EMPTY_PAYLOAD = "empty_payload"
    NO_EVIDENCE = "no_evidence"
    UNSEALED = "unsealed_with_evidence"


@dataclass
class Finding:
    path: Path
    entry_index: object
    kind: str
    declared: Optional[str]
    computed: Optional[str]
    detail: str


def hexdump(data: bytes, offset: int = 0, width: int = 16) -> str:
    out = []
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hx = " ".join(f"{b:02x}" for b in chunk).ljust(width * 3 - 1)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"{offset + i:08x}  {hx}  |{asc}|")
    return "\n".join(out)


def _hex_or_bytes(s: str) -> bytes:
    if len(s) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in s):
        return bytes.fromhex(s)
    return s.encode("utf-8")


def hex_seal_diff(declared: str, computed: str) -> str:
    d = _hex_or_bytes(declared)
    c = _hex_or_bytes(computed)
    lines = [
        f"declared  ({len(d):3d} bytes):",
        hexdump(d),
        "",
        f"computed  ({len(c):3d} bytes):",
        hexdump(c),
        "",
    ]
    if d == c:
        lines.append("bytes identical -- seal matches")
        return "\n".join(lines)
    n = min(len(d), len(c))
    for i in range(n):
        if d[i] != c[i]:
            lines.append(
                f"first divergence at byte {i}: "
                f"declared {d[i]:02x}  vs  computed {c[i]:02x}"
            )
            break
    else:
        lines.append(f"prefix identical; lengths differ ({len(d)} vs {len(c)})")
    return "\n".join(lines)


def load_entry(path: Path) -> Optional[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        import yaml  # type: ignore

        obj = yaml.safe_load(text)
    except ImportError:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
    except Exception:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
    return obj if isinstance(obj, dict) else None


def _evidence_of(entry: dict) -> Optional[list]:
    ev = entry.get("evidence_at_seal_time")
    if isinstance(ev, list):
        return ev
    impl = entry.get("implementation_status")
    if isinstance(impl, dict):
        ev = impl.get("evidence_at_seal_time")
        if isinstance(ev, list):
            return ev
    return None


def iter_entries(root: Path) -> Iterator[Path]:
    # Must use *.yaml — rglob(".yaml") matches only a file literally named .yaml
    for pat in ("*.yaml", "*.yml"):
        yield from sorted(root.rglob(pat))


def scan(root: Path, include_drafts: bool = False) -> List[Finding]:
    findings: List[Finding] = []

    for path in iter_entries(root):
        entry = load_entry(path)
        if entry is None:
            continue

        status = entry.get("status", "")
        declared = entry.get("seal")
        payload = entry.get("payload")
        evidence = _evidence_of(entry)
        idx = entry.get("entry_index", entry.get("entry"))

        if not include_drafts and status == "DRAFT":
            continue

        if declared and not payload:
            findings.append(
                Finding(
                    path,
                    idx,
                    Kind.EMPTY_PAYLOAD,
                    declared if isinstance(declared, str) else str(declared),
                    None,
                    "seal asserted with no payload to verify against",
                )
            )
            continue

        if declared and isinstance(payload, dict):
            computed = compute_seal(payload)
            if computed != declared:
                findings.append(
                    Finding(
                        path,
                        idx,
                        Kind.FORGED,
                        declared if isinstance(declared, str) else str(declared),
                        computed,
                        "declared seal does not match recomputed seal",
                    )
                )

        if declared and evidence is not None and not evidence:
            findings.append(
                Finding(
                    path,
                    idx,
                    Kind.NO_EVIDENCE,
                    declared if isinstance(declared, str) else str(declared),
                    None,
                    "seal present but evidence_at_seal_time is empty",
                )
            )

        if evidence and not declared:
            findings.append(
                Finding(
                    path,
                    idx,
                    Kind.UNSEALED,
                    None,
                    None,
                    "evidence present but no seal -- entry is unsealed",
                )
            )

    return findings


def render(findings: List[Finding], with_hex: bool) -> str:
    lines = [
        f"hexstrike -- {CATALOGUED_CLASS} scan",
        f"algorithm: {SEAL_ALGORITHM}",
        f"findings : {len(findings)}",
        "=" * 64,
    ]
    if not findings:
        lines.append("no ghost seals found")
        return "\n".join(lines)

    for f in findings:
        lines.append("")
        lines.append(f"  {f.path}")
        lines.append(f"    entry_index : {f.entry_index}")
        lines.append(f"    class       : {CATALOGUED_CLASS}/{f.kind}")
        lines.append(f"    detail      : {f.detail}")
        lines.append(f"    declared    : {f.declared}")
        lines.append(f"    computed    : {f.computed}")
        if with_hex and f.kind == Kind.FORGED and f.declared and f.computed:
            lines.append("")
            lines.append(hex_seal_diff(f.declared, f.computed))
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Hex inspection targeting the catalogued ghost-seal defect."
    )
    ap.add_argument("root", type=Path, help="ledger root to scan")
    ap.add_argument(
        "--hex", action="store_true", help="byte-level hexdump for forged seals"
    )
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument(
        "--include-drafts",
        action="store_true",
        help="scan DRAFT entries too (default: skip)",
    )
    args = ap.parse_args(argv)

    if not args.root.exists():
        print(f"not found: {args.root}", file=sys.stderr)
        return 2

    findings = scan(args.root, include_drafts=args.include_drafts)

    if args.json:
        print(
            json.dumps(
                {
                    "class": CATALOGUED_CLASS,
                    "algorithm": SEAL_ALGORITHM,
                    "findings": [
                        {
                            "path": str(f.path),
                            "entry_index": f.entry_index,
                            "kind": f.kind,
                            "declared": f.declared,
                            "computed": f.computed,
                            "detail": f.detail,
                        }
                        for f in findings
                    ],
                },
                indent=2,
            )
        )
    else:
        print(render(findings, args.hex))

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
