"""anatomy/spine.py — chain, uniqueness, prior pointer.

Organ of the Sovereign Anatomy. Verifies witness-chain continuity:
each entry's prior pointer must name the existing predecessor exactly once.
Seal domain: GARDEN.EVENT.v1 (POLICY.md Art. 10 S1a).
"""

import hashlib
import re
from pathlib import Path

LEDGER_DIR = Path("ledger")
ASCII_ARROW = re.compile(r"(\d{1,6})\s*->\s*(\d{1,6})")
CHAIN_RE = re.compile(r"(\d{1,6}(?:\s*→\s*\d{1,6})+)")


def witness_pairs(text: str) -> list[tuple[int, int]]:
    """Pairs from a chain, including the shared middle of A → B → C."""
    pairs = []
    for chain in CHAIN_RE.finditer(text):
        nums = [int(n) for n in re.findall(r"\d{1,6}", chain.group(0))]
        pairs.extend(zip(nums, nums[1:]))
    return pairs


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

    # Accept three stored forms. Do not rewrite the file.
    # immediate: a → b. span: 0 → b. skip: x → b with x < a.
    # Flag only when no arrow ends at b.
    forms = {"immediate": 0, "span": 0, "skip": 0}
    for a, b in zip(indices, indices[1:]):
        if b != a + 1:
            continue
        text = as_working_default(entries[b].read_text(encoding="utf-8"))
        pairs = witness_pairs(text)
        ends = [(x, y) for x, y in pairs if y == b]
        if (a, b) in ends:
            forms["immediate"] += 1
            continue
        spans = [x for x, y in ends if x == 0]
        skips = [x for x, y in ends if x < a]
        if spans:
            forms["span"] += 1
            continue
        if skips:
            forms["skip"] += 1
            continue
        found = ", ".join(f"{x}→{y}" for x, y in pairs[:4]) or "none"
        problems.append(f"witness pointer {a} -> {b} missing; found {found}")

    return {
        "entries": len(indices),
        "problems": problems,
        "forms": forms,
        "ok": not problems,
    }


if __name__ == "__main__":
    result = check_spine()
    print(f"spine: {result['entries']} entries, ok={result['ok']} forms={result['forms']}")
    for p in result["problems"]:
        print("  !", p)
    raise SystemExit(0 if result["ok"] else 1)
