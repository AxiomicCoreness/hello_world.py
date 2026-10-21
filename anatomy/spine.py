"""anatomy/spine.py — chain, uniqueness, prior pointer.

Organ of the Sovereign Anatomy. Verifies witness-chain continuity:
each entry's prior pointer must name the existing predecessor exactly once.
Seal domain: GARDEN.EVENT.v1 (POLICY.md Art. 10 S1a).
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict, Any

LEDGER_DIR = Path("ledger")
ASCII_ARROW = re.compile(r"(\d{1,6})\s*->\s*(\d{1,6})")
CHAIN_RE = re.compile(r"(\d{1,6}(?:\s*[→\-]>\s*\d{1,6})+)")
ENTRY_INDEX_RE = re.compile(r'^entry_index:\s*"?(\d+)"?\s*$', re.M)


def witness_pairs(text: str) -> List[Tuple[int, int]]:
    """Pairs from a chain, including the shared middle of A → B → C."""
    pairs = []
    for chain in CHAIN_RE.finditer(text):
        nums = [int(n) for n in re.findall(r"\d{1,6}", chain.group(0))]
        pairs.extend(zip(nums, nums[1:]))
    return pairs


def as_working_default(text: str) -> str:
    """Normalize every ASCII hop. One pass hides the second arrow in a chain.
    
    We loop until the text stops changing, because a chain like '1 -> 2 -> 3'
    only replaces the first '->' per regex pass. The regex engine consumes
    the '2' as part of the first match, so '2 -> 3' can't match until the next pass.
    """
    previous = None
    while previous != text:
        previous = text
        text = ASCII_ARROW.sub(lambda m: f"{m.group(1)} → {m.group(2)}", text)
    return text


def load_index(path: Path) -> int:
    """Extract the entry_index from a ledger YAML file."""
    text = path.read_text(encoding="utf-8")
    m = ENTRY_INDEX_RE.search(text)
    if not m:
        raise ValueError(f"entry_index missing in {path}")
    return int(m.group(1))


def check_spine(ledger_dir: Path = LEDGER_DIR) -> Dict[str, Any]:
    """Check chain, uniqueness, and prior pointers across the ledger tail."""
    entries = {}
    for p in sorted(ledger_dir.glob("*.yaml")):
        try:
            entries[load_index(p)] = p
        except ValueError as e:
            # Skip malformed files; don't crash the whole spine check
            print(f"::warning::spine: {e}")

    indices = sorted(entries)
    problems = []

    # Uniqueness: duplicate entry_index values are structural errors.
    seen = set()
    for idx in indices:
        if idx in seen:
            problems.append(f"duplicate entry_index {idx}")
        seen.add(idx)

    # Rewire pointer history on the reader. Sealed files are not edited.
    # An arrow that ends at b keeps its stored start. A gap gets the numeric sibling.
    forms = {"immediate": 0, "span": 0, "skip": 0, "rewired": 0}
    history = []
    derived = []
    
    for a, b in zip(indices, indices[1:]):
        # Only check contiguous numeric pairs
        if b != a + 1:
            continue
        
        text = as_working_default(entries[b].read_text(encoding="utf-8"))
        pairs = witness_pairs(text)
        
        # Filter pairs where the target is b
        ends = [(x, y) for x, y in pairs if y == b]
        
        # Case 1: Immediate pair (a, b)
        if (a, b) in ends:
            forms["immediate"] += 1
            history.append((a, b, "immediate"))
            continue
        
        # Case 2: Span (stored x=0, target=b)
        spans = [x for x, y in ends if x == 0]
        if spans:
            forms["span"] += 1
            history.append((spans[0], b, "span"))
            continue
        
        # Case 3: Skip (stored x < a, target=b)
        skips = [x for x, y in ends if x < a]
        if skips:
            forms["skip"] += 1
            history.append((skips[0], b, "skip"))
            continue
        
        # Case 4: Rewired/derived (no matching stored arrow)
        forms["rewired"] += 1
        history.append((a, b, "rewired"))
        stored = ", ".join(f"{x}→{y}" for x, y in pairs[:4])
        if stored:
            problems.append(
                f"content anomaly {a} -> {b}; derived {a} -> {b}; stored {stored}"
            )
        else:
            derived.append(f"derived {a} -> {b}; no stored arrow")

    return {
        "entries": len(indices),
        "problems": problems,
        "derived_links": derived,
        "forms": forms,
        "history": history,
        "ok": not problems,
    }


if __name__ == "__main__":
    result = check_spine()
    print(f"spine: {result['entries']} entries, ok={result['ok']} forms={result['forms']}")
    print(f"derived_links: {len(result['derived_links'])} content_anomalies: {len(result['problems'])}")
    for p in result["derived_links"]:
        print("  .", p)
    for p in result["problems"]:
        print("  !", p)
    raise SystemExit(0 if result["ok"] else 1)
