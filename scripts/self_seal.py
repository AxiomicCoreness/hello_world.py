#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The code block that writes itself.

A signitorial seal: a document carries its own digest, computed over its
own bytes with the seal block held at a fixed placeholder. The seal
participates in the document without participating in its own hash.

Two seal kinds in this stack:

  ledger seal   — SHA3-256 over canonical JSON of an entry body,
                  digest appended: "<prefix> · <label> · <digest>"
                  see: scripts/verify_ledger.py

  signitorial   — SHA3-256 over raw document bytes, seal block masked,
                  four fields: Integrity / Seal / Witness / Combined
                  see: this file

Different instruments. A ledger seal proves entry continuity. A
signitorial seal proves document integrity against post-hoc edit.
Neither authenticates against a third party — for that, sign the commit.

Field names describe values, not promises:
  Integrity — SHA3-256 of the masked document body
  Seal      — SHA3-256 over (Integrity | filename | placeholder)
  Witness   — HMAC over Seal under a derived key; drift detector
  Combined  — SHA3-256 over the three above; presence, not authentication

Usage:
  python3 scripts/self_seal.py sign   README.md NOTICE PROVENANCE.md
  python3 scripts/self_seal.py verify README.md NOTICE PROVENANCE.md
  python3 scripts/self_seal.py check  README.md NOTICE PROVENANCE.md
"""

from __future__ import annotations

import hashlib
import hmac
import re
import sys
from pathlib import Path

BEGIN = "<!-- SEAL:BEGIN -->"
END = "<!-- SEAL:END -->"
PLACEHOLDER = "<PENDING>"

FIELDS = ("Integrity", "Seal", "Witness", "Combined")

FIELD_RE = re.compile(
    r"^\s*(Integrity|Seal|Witness|Combined):\s*(\S*)\s*$",
    re.MULTILINE,
)


def _block_body(fields: dict[str, str] | None = None) -> str:
    """Render the interior of the seal block. All four fields, always."""
    values = fields or {name: PLACEHOLDER for name in FIELDS}
    body = "\n"
    for name in FIELDS:
        body += f"  {name}: {values.get(name, PLACEHOLDER)}\n"
    body += "\n"
    return body


def _seed(path: Path) -> str:
    """
    Guarantee the block is present and fully populated with placeholders.
    Returns the seeded text. Idempotent.
    """
    text = path.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        raise SystemExit(f"❌ {path}: missing {BEGIN} / {END} markers")

    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return head + BEGIN + _block_body() + END + tail


def _masked(path: Path) -> str:
    """
    Document text with every seal field reset to the placeholder.
    Seed first, so an empty or partially-filled block still masks cleanly.
    """
    seeded = _seed(path)

    head, rest = seeded.split(BEGIN, 1)
    body, tail = rest.split(END, 1)
    body = FIELD_RE.sub(lambda m: f"{m.group(1)}: {PLACEHOLDER}", body)
    return head + BEGIN + body + END + tail


def _digest(data: str) -> str:
    return hashlib.sha3_256(data.encode("utf-8")).hexdigest()


def compute(path: Path) -> dict[str, str]:
    masked = _masked(path)

    integrity = _digest(masked)
    label = path.name
    seal = _digest(f"{integrity}|{label}|{PLACEHOLDER}")

    key = _digest(f"GARDEN.SIGNITORIAL.v1|{label}")[:32].encode()
    witness = hmac.new(key, seal.encode(), hashlib.sha3_256).hexdigest()

    combined = _digest(f"{integrity}|{seal}|{witness}")

    return {
        "Integrity": integrity,
        "Seal": seal,
        "Witness": witness,
        "Combined": combined,
    }


def sign(path: Path) -> None:
    # Write placeholders first so the masked body is well-defined,
    # then compute against that exact body, then write real values.
    path.write_text(_seed(path), encoding="utf-8")

    fields = compute(path)

    text = path.read_text(encoding="utf-8")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)

    path.write_text(head + BEGIN + _block_body(fields) + END + tail,
                    encoding="utf-8")

    print(f"✅ signed {path}")
    for name in FIELDS:
        print(f"   {name:<10} {fields[name][:32]}…")


def verify(path: Path) -> bool:
    expected = compute(path)
    text = path.read_text(encoding="utf-8")

    _, rest = text.split(BEGIN, 1)
    body, _ = rest.split(END, 1)

    found = {m.group(1): m.group(2) for m in FIELD_RE.finditer(body)}

    ok = True
    for name in FIELDS:
        if found.get(name) != expected[name]:
            print(f"❌ {path}: {name} mismatch")
            print(f"   found:    {found.get(name)}")
            print(f"   expected: {expected[name]}")
            ok = False

    if ok:
        print(f"✅ {path}: signitorial seal intact")
        print(f"   Combined: {found['Combined'][:32]}…")
    return ok


def check(path: Path, needle: str = "Clarke Yoursa Tee") -> bool:
    """
    Byte-position check: is the name inside the masked region — i.e. in
    the body above SEAL:BEGIN, where the hash sees it?
    """
    masked = _masked(path)
    head, _ = masked.split(BEGIN, 1)
    present = needle in head

    print(f"{str(path):16} name-in-masked-body: {present}")
    if not present:
        print(f"   ⚠️  move one line with '{needle}' above {BEGIN}")
    return present


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("sign", "verify", "check"):
        print(__doc__)
        return 2

    verb, targets = argv[1], [Path(p) for p in argv[2:]]

    if verb == "sign":
        for p in targets:
            sign(p)
        return 0

    if verb == "verify":
        failed = sum(0 if verify(p) else 1 for p in targets)
        print("-" * 60)
        print(f"checked={len(targets)}  failed={failed}")
        return 1 if failed else 0

    # check
    results = [check(p) for p in targets]
    print("-" * 60)
    print(f"checked={len(targets)}  in-digest={sum(results)}  missing={len(results) - sum(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
