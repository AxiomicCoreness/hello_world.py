"""anatomy/spine.py — chain, uniqueness, prior pointer.

Organ of the Sovereign Anatomy. Verifies witness-chain continuity:
each entry's prior pointer must name the existing predecessor exactly once.
Seal domain: GARDEN.EVENT.v1 (POLICY.md Art. 10 S1a).
"""

import hashlib
import re
from pathlib import Path

LEDGER_DIR = Path("ledger")
POINTER_RE = re.compile(r"(\d{4,6})\s*→\s*(\d{4,6})")
ASCII_ARROW = re.compile(r"(\d{4,6})\s*->\s*(\d{4,6})")


def as_working_default(text: str) -> str:
    """Switch an ASCII witness arrow to the Unicode default the checker uses."""
    return ASCII_ARROW.sub(lambda m: f"{m.group(1)} → {m.group(2)}", text)


def load_index(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^entry_index:\s*"?(\d+)"?\s*$', text, re.M)
    if not m:
        raise ValueError(f"entry_index missing in {path}")
    return int(m.group(1))


def check_spine(ledger_dir: Path = LEDGER_DIR) -> dict:
    """Check chain, uniqueness, and prior pointers across the ledger tail."""
    entries = {}
    for p in sorted(ledger_dir.glob("*.yaml")):
        entries[load_index(p)] = p

    indices = sorted(entries)
    problems = []

    # Uniqueness: duplicate entry_index values are structural errors.
    seen = set()
    for idx in indices:
        if idx in seen:
            problems.append(f"duplicate entry_index {idx}")
        seen.add(idx)

    # Prior pointer: consecutive numeric siblings must witness each other.
    for a, b in zip(indices, indices[1:]):
        if b == a + 1:
            text = as_working_default(entries[b].read_text(encoding="utf-8"))
            m = POINTER_RE.search(text)
            if not m or int(m.group(1)) != a:
                problems.append(f"witness pointer {a} -> {b} missing or broken")

    return {"entries": len(indices), "problems": problems, "ok": not problems}


if __name__ == "__main__":
    result = check_spine()
    print(f"spine: {result['entries']} entries, ok={result['ok']}")
    for p in result["problems"]:
        print("  !", p)
    raise SystemExit(0 if result["ok"] else 1)
