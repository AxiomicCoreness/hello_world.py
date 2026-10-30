#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""hexstrike.py — ghost-seal scanner for append-only ledger entries.

Defect class: ghost_seal
Subtypes (byte-level):
  forged_seal              declared seal != recomputed seal over payload
  empty_payload            seal asserted, payload absent
  no_evidence              seal present, evidence_at_seal_time empty list
  unsealed_with_evidence   evidence present, seal is null/absent

Extra metrics are counted in the same walk. No second pass.

Pure stdlib. Optional PyYAML if installed; otherwise JSON-only parse.
Exit: 0 clean, 1 findings, 2 usage/IO or incomplete scan.

Incomplete scan: if any entry cannot be parsed (for example PyYAML is not
importable under `python -I` while the ledger holds YAML entries), the scan
exits 2 and names the count and cause instead of reporting a pass. Per-file
failures are listed in --json under "parse_failures". An entry that is
genuinely malformed and cannot be edited (the ledger is append-only) may be
listed in a --known-unparsed file; it is still reported as KNOWN-UNPARSED.
A missing PyYAML is never excusable that way.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

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


@dataclass
class Metrics:
    files_seen: int = 0
    parsed: int = 0
    unparsed: int = 0
    drafts_skipped: int = 0
    sealed: int = 0
    findings: int = 0
    by_kind: dict = field(default_factory=dict)
    known_unparsed: int = 0
    parse_failures: List["ParseFailure"] = field(default_factory=list)

    @property
    def blocking_unparsed(self) -> int:
        return self.unparsed - self.known_unparsed

    def as_dict(self) -> dict:
        return {
            "files_seen": self.files_seen,
            "parsed": self.parsed,
            "unparsed": self.unparsed,
            "known_unparsed": self.known_unparsed,
            "blocking_unparsed": self.blocking_unparsed,
            "drafts_skipped": self.drafts_skipped,
            "sealed": self.sealed,
            "findings": self.findings,
            "by_kind": self.by_kind,
        }


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


class ParseReason:
    READ_ERROR = "read_error"
    YAML_UNAVAILABLE = "yaml_unavailable"
    PARSE_ERROR = "parse_error"
    NOT_A_MAPPING = "not_a_mapping"


def yaml_available() -> bool:
    try:
        import yaml  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


def parse_entry(path: Path) -> Tuple[Optional[dict], Optional[str], str]:
    """Parse one entry. Returns (entry, reason, detail).

    entry is None when the file could not be read as a mapping; reason is one of
    ParseReason and detail is a human-readable cause. Parsing itself is
    unchanged: PyYAML when importable, JSON as the fallback.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return None, ParseReason.READ_ERROR, str(e)
    try:
        import yaml  # type: ignore
    except ImportError:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            return (
                None,
                ParseReason.YAML_UNAVAILABLE,
                f"PyYAML not importable and file is not JSON ({e.msg})",
            )
    else:
        try:
            obj = yaml.safe_load(text)
        except Exception as e:
            yaml_err = " ".join(str(e).split())
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                return None, ParseReason.PARSE_ERROR, f"YAML: {yaml_err}"
    if not isinstance(obj, dict):
        return None, ParseReason.NOT_A_MAPPING, f"top level is {type(obj).__name__}"
    return obj, None, ""


def load_entry(path: Path) -> Optional[dict]:
    entry, _reason, _detail = parse_entry(path)
    return entry


@dataclass
class ParseFailure:
    path: Path
    reason: str
    detail: str
    known: bool = False


def load_known_unparsed(list_file: Path) -> Dict[str, str]:
    """Read a known-unparsed list: one path per line, optional '# note'.

    Paths are resolved against the list file's repository root (the parent of
    its directory, i.e. scripts/..), so entries read like `ledger/9128.yaml`.
    Only `parse_error` / `not_a_mapping` failures can be excused by this list;
    a missing PyYAML or an unreadable file never can.
    """
    base = list_file.resolve().parent.parent
    known: Dict[str, str] = {}
    for raw in list_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rel, _, note = line.partition("#")
        rel = rel.strip()
        known[str((base / rel).resolve())] = note.strip()
    return known


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
    for pat in ("*.yaml", "*.yml"):
        yield from sorted(root.rglob(pat))


_EXCUSABLE = (ParseReason.PARSE_ERROR, ParseReason.NOT_A_MAPPING)


def scan(
    root: Path,
    include_drafts: bool = False,
    known_unparsed: Optional[Dict[str, str]] = None,
) -> tuple[List[Finding], Metrics]:
    findings: List[Finding] = []
    metrics = Metrics()
    known_unparsed = known_unparsed or {}

    for path in iter_entries(root):
        metrics.files_seen += 1
        entry, reason, detail = parse_entry(path)
        if entry is None:
            metrics.unparsed += 1
            known = reason in _EXCUSABLE and str(path.resolve()) in known_unparsed
            if known:
                metrics.known_unparsed += 1
            metrics.parse_failures.append(
                ParseFailure(path, reason or "", detail, known)
            )
            continue
        metrics.parsed += 1

        status = entry.get("status", "")
        declared = entry.get("seal")
        payload = entry.get("payload")
        evidence = _evidence_of(entry)
        idx = entry.get("entry_index", entry.get("entry"))

        if not include_drafts and status == "DRAFT":
            metrics.drafts_skipped += 1
            continue

        if declared:
            metrics.sealed += 1

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

    metrics.findings = len(findings)
    for item in findings:
        metrics.by_kind[item.kind] = metrics.by_kind.get(item.kind, 0) + 1
    return findings, metrics


def render(findings: List[Finding], metrics: Metrics, with_hex: bool) -> str:
    lines = [
        f"hexstrike -- {CATALOGUED_CLASS} scan",
        f"algorithm: {SEAL_ALGORITHM}",
        f"files_seen: {metrics.files_seen}",
        f"parsed    : {metrics.parsed}",
        f"unparsed  : {metrics.unparsed}"
        f" (known: {metrics.known_unparsed}, blocking: {metrics.blocking_unparsed})",
        f"drafts    : {metrics.drafts_skipped}",
        f"sealed    : {metrics.sealed}",
        f"findings  : {metrics.findings}",
        f"by_kind   : {json.dumps(metrics.by_kind, sort_keys=True)}",
        "=" * 64,
    ]
    for pf in metrics.parse_failures:
        tag = "KNOWN-UNPARSED" if pf.known else "UNPARSED"
        lines.append(f"  {tag} {pf.path}: {pf.reason}: {pf.detail}")
    if metrics.parse_failures:
        lines.append("=" * 64)
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
    ap.add_argument(
        "--known-unparsed",
        type=Path,
        default=None,
        metavar="LIST",
        help=(
            "file listing entries already known not to parse (one repo-relative "
            "path per line, '# note' allowed). Listed parse errors are reported "
            "as KNOWN-UNPARSED instead of forcing exit 2. Never excuses a "
            "missing PyYAML."
        ),
    )
    args = ap.parse_args(argv)

    if not args.root.exists():
        print(f"not found: {args.root}", file=sys.stderr)
        return 2

    known: Dict[str, str] = {}
    if args.known_unparsed is not None:
        if not args.known_unparsed.is_file():
            print(f"known-unparsed list not found: {args.known_unparsed}", file=sys.stderr)
            return 2
        known = load_known_unparsed(args.known_unparsed)

    findings, metrics = scan(
        args.root, include_drafts=args.include_drafts, known_unparsed=known
    )

    if args.json:
        print(
            json.dumps(
                {
                    "class": CATALOGUED_CLASS,
                    "algorithm": SEAL_ALGORITHM,
                    "metrics": metrics.as_dict(),
                    "yaml_available": yaml_available(),
                    "known_unparsed_list": (
                        str(args.known_unparsed) if args.known_unparsed else None
                    ),
                    "parse_failures": [
                        {
                            "path": str(pf.path),
                            "reason": pf.reason,
                            "detail": pf.detail,
                            "known": pf.known,
                        }
                        for pf in metrics.parse_failures
                    ],
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
        print(render(findings, metrics, args.hex))

    if metrics.blocking_unparsed:
        print(incomplete_message(metrics), file=sys.stderr)
        return 2
    return 0 if not findings else 1


def incomplete_message(metrics: Metrics) -> str:
    """Why a scan with unparsed entries refuses to pass (exit 2)."""
    blocking = [pf for pf in metrics.parse_failures if not pf.known]
    by_reason: Dict[str, int] = {}
    for pf in blocking:
        by_reason[pf.reason] = by_reason.get(pf.reason, 0) + 1
    parts = [
        f"hexstrike: INCOMPLETE SCAN -- {len(blocking)} of {metrics.files_seen} "
        f"ledger entries could not be parsed ({json.dumps(by_reason, sort_keys=True)}); "
        "refusing to report a pass."
    ]
    if by_reason.get(ParseReason.YAML_UNAVAILABLE):
        parts.append(
            "cause: PyYAML is not importable in this interpreter "
            f"({sys.executable}; e.g. `python -I` hides the user site-packages), "
            "so YAML entries fell back to JSON and failed."
        )
    for pf in blocking[:5]:
        parts.append(f"  {pf.path}: {pf.reason}: {pf.detail}")
    if len(blocking) > 5:
        parts.append(f"  ... and {len(blocking) - 5} more (see --json parse_failures)")
    return "\n".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
