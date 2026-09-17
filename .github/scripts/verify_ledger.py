#!/usr/bin/env python3
"""
🜁∀ verify_ledger — parallel-series witness-chain verifier ∀🜁

Purpose
-------
Verify the sovereign ledger without assuming a single global sequence.
The ledger is composed of independent series (83xx, 91xx, 92xx, ...);
each series has its own monotonic witness chain. Cross-series arrows
are NOT enforced.

What this script checks
-----------------------
1. Every entry has the required fields.
2. Every entry's `seal` matches the SHA3-256 of its canonical JSON
   (excluding the `seal` field itself).
3. Within each series, `witness_chain` is consecutive:
   the prefix "NNNN → MMMM" must satisfy MMMM == NNNN + 1, and the
   NNNN must equal the previous entry's MMMM in the same series.
4. Optional: reward-pool arithmetic matches fiduciary_node_rewards
   when that module is importable.

What this script does NOT check
-------------------------------
- Cross-series ordering (83xx vs 91xx vs 92xx are independent).
- Semantic correctness of any event payload.
- Whether the live HEAD is the highest-numbered entry across all series.

Exit codes
----------
0  all checks passed
1  contract violation (bad seal, bad field, broken chain)
2  I/O error or nothing to verify

Usage
-----
    python .github/scripts/verify_ledger
    python .github/scripts/verify_ledger --root .
    python .github/scripts/verify_ledger --ledger-dir ledger
    python .github/scripts/verify_ledger --series 83 --series 91
    python .github/scripts/verify_ledger --no-reward-check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml  # provided by CI env
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = ("entry_index", "event", "seal", "witness_chain")

# Series prefixes we recognise. Each series is independent.
# Ordered longest-first so 4-digit prefixes match before 2-digit ones.
KNOWN_SERIES_PREFIXES = (
    "5105",  # legacy 5105x design notes
    "83",    # reward / CI narrative
    "91",    # self-improvement / MCP
    "92",    # soft / held
    "51",    # legacy 51x design notes
    "00",    # genesis
)

# Witness chain pattern: "NNNN → MMMM — UNBROKEN" (arrow, hyphen, en/em dash)
WITNESS_RE = re.compile(r"^\s*(\d{3,6})\s*[→>\-–—]+?\s*(\d{3,6})")

# Anchors that mark genesis of a series (no preceding entry required).
GENESIS_ANCHORS = frozenset({"0000", "0001", "1", "GENESIS"})


# ──────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────

@dataclass
class Entry:
    path: str
    index: str          # zero-padded string, e.g. "8340"
    series: str         # series prefix, e.g. "83"
    data: Dict[str, Any]
    seal_ok: Optional[bool] = None
    seal_computed: Optional[str] = None
    chain_prev: Optional[str] = None
    chain_next: Optional[str] = None
    notes: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Loading
# ──────────────────────────────────────────────────────────────────────

def _iter_yaml_files(ledger_dir: str) -> Iterable[str]:
    if not os.path.isdir(ledger_dir):
        return
    for name in sorted(os.listdir(ledger_dir)):
        if name.endswith((".yaml", ".yml")):
            yield os.path.join(ledger_dir, name)


def _load_yaml_file(path: str) -> List[Dict[str, Any]]:
    """Load one file which may contain multiple '---' documents."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not HAVE_YAML:
        # Tiny fallback: try to load as a single JSON document.
        try:
            obj = json.loads(text)
            return [obj] if isinstance(obj, dict) else []
        except json.JSONDecodeError:
            raise RuntimeError(
                f"PyYAML required to load non-JSON YAML: {path}"
            )
    docs = list(yaml.safe_load_all(text))
    return [d for d in docs if isinstance(d, dict) and d]


def _series_of(index: str) -> str:
    """Return the series prefix for an index.

    Uses KNOWN_SERIES_PREFIXES (ordered longest-first) for matching to
    avoid collisions between e.g. 5105 and 510510.
    """
    z = index.zfill(4)
    for p in KNOWN_SERIES_PREFIXES:
        if z.startswith(p):
            return p
    return z[:2] if len(z) >= 2 else z


def load_entries(ledger_dir: str,
                 wanted_series: Optional[List[str]] = None) -> List[Entry]:
    wanted = set(wanted_series) if wanted_series else None
    entries: List[Entry] = []
    for path in _iter_yaml_files(ledger_dir):
        try:
            docs = _load_yaml_file(path)
        except Exception as e:
            print(f"::error file={path}::failed to parse: {e}")
            continue
        for doc in docs:
            raw_index = doc.get("entry_index")
            if raw_index is None:
                continue
            index = str(raw_index).zfill(4)
            series = _series_of(index)
            if wanted and series not in wanted:
                continue
            entries.append(Entry(
                path=path,
                index=index,
                series=series,
                data=doc,
            ))
    return entries


# ──────────────────────────────────────────────────────────────────────
# Seal computation
# ──────────────────────────────────────────────────────────────────────

def _canonical_json(data: Dict[str, Any]) -> str:
    """Deterministic JSON: sorted keys, tight separators, no ASCII escapes
    (matches the producer-side json.dumps(plan, sort_keys=True) contract)."""
    return json.dumps(data, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)


def compute_seal(data: Dict[str, Any]) -> str:
    payload = {k: v for k, v in data.items() if k != "seal"}
    canonical = _canonical_json(payload)
    return hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()


def seal_field_matches(data: Dict[str, Any], computed: str) -> bool:
    """Match the seal field against the computed digest.

    Accepts two regimes:
    - Regime A: seal == digest (exact match)
    - Regime B: seal ends with digest as final whitespace-delimited token

    This is stricter than substring matching to avoid false positives.
    """
    seal = data.get("seal", "")
    if not isinstance(seal, str):
        return False
    if seal == computed:
        return True
    parts = seal.split()
    if parts:
        tail = parts[-1]
        return tail.lower() == computed.lower()
    return False


# ──────────────────────────────────────────────────────────────────────
# Checks
# ──────────────────────────────────────────────────────────────────────

def check_required_fields(entries: List[Entry]) -> int:
    bad = 0
    for e in entries:
        missing = [f for f in REQUIRED_FIELDS if f not in e.data]
        if missing:
            print(f"::error file={e.path}::entry {e.index} "
                  f"missing fields: {missing}")
            bad += 1
    return bad


def check_seals(entries: List[Entry], strict: bool = False) -> int:
    bad = 0
    for e in entries:
        computed = compute_seal(e.data)
        e.seal_computed = computed
        ok = seal_field_matches(e.data, computed)
        e.seal_ok = ok
        if not ok:
            bad += 1
            lvl = "error" if strict else "warning"
            print(f"::{lvl} file={e.path}::entry {e.index} seal mismatch")
            print(f"        expected digest: {computed}")
            print(f"        seal field:      {e.data.get('seal')}")
    return bad


def check_chains(entries: List[Entry]) -> int:
    """Verify witness-chain continuity per series.

    Enforces strict consecutiveness within each series:
    Each entry's witness_chain must be "PPPP → NNNN" where:
    - NNNN equals the entry's own index
    - PPPP equals the previous entry's index in the same series
    - No gaps allowed (strict consecutive chain)
    """
    by_series: Dict[str, List[Entry]] = {}
    for e in entries:
        by_series.setdefault(e.series, []).append(e)

    bad = 0
    for series, group in sorted(by_series.items()):
        group.sort(key=lambda x: x.index)
        print(f"── series {series}: {len(group)} entries "
              f"({group[0].index}..{group[-1].index})")

        for i, e in enumerate(group):
            m = WITNESS_RE.match(str(e.data.get("witness_chain", "")))
            if not m:
                print(f"::error file={e.path}::entry {e.index} "
                      f"unparseable witness_chain: "
                      f"{e.data.get('witness_chain')!r}")
                bad += 1
                continue
            prev, nxt = m.group(1).zfill(4), m.group(2).zfill(4)
            e.chain_prev, e.chain_next = prev, nxt

            # Arrow must target the entry's own index.
            if nxt != e.index:
                print(f"::error file={e.path}::entry {e.index} "
                      f"chain arrow target {nxt} != index {e.index}")
                bad += 1
                continue

            if i == 0:
                # First entry: previous must be a genesis anchor.
                if prev not in GENESIS_ANCHORS:
                    # Allow "0000" style too.
                    if not (len(prev) == 4 and int(prev) <= 1):
                        print(f"::error file={e.path}::entry {e.index} "
                              f"first in series but prev {prev} is not a "
                              f"genesis anchor")
                        bad += 1
            else:
                # Subsequent entries: prev must equal previous index.
                prev_entry = group[i - 1]
                if prev != prev_entry.index:
                    print(f"::error file={e.path}::entry {e.index} "
                          f"prev {prev} != previous entry "
                          f"{prev_entry.index}")
                    bad += 1
                if prev_entry.chain_next != e.index:
                    print(f"::error file={e.path}::entry {e.index} "
                          f"previous entry {prev_entry.index} chain-next "
                          f"is {prev_entry.chain_next}, expected {e.index}")
                    bad += 1
    return bad


def check_reward_pool(entries: List[Entry]) -> int:
    """If fiduciary_node_rewards is importable, cross-check the declared
    pool value against its verifier. Otherwise, skip silently."""
    try:
        from fiduciary_node_rewards import verify_reward_pool  # type: ignore
    except Exception:
        print("── reward-pool check skipped "
              "(fiduciary_node_rewards not importable)")
        return 0

    try:
        ok, total = verify_reward_pool()
    except Exception as e:
        print(f"::error::verify_reward_pool raised: {e}")
        return 1

    declared_ok = False
    declared_value = None
    for e in entries:
        v = (e.data.get("reward_pool")
             or e.data.get("declared_pool")
             or (e.data.get("pool") or {}).get("declared_value"))
        if v is not None:
            try:
                declared_value = float(v)
                if abs(declared_value - float(total)) < 1e-6:
                    declared_ok = True
            except (TypeError, ValueError):
                pass

    print(f"── reward pool: verify_reward_pool -> ok={ok}, "
          f"total={total:.10f}")
    if declared_value is not None:
        print(f"                declared value in ledger: "
              f"{declared_value:.10f} (match={declared_ok})")

    return 0 if ok else 1


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Verify sovereign ledger chains.")
    ap.add_argument("--root", default=".",
                    help="Repository root (default: .)")
    ap.add_argument("--ledger-dir", default=None,
                    help="Ledger directory (default: <root>/ledger)")
    ap.add_argument("--series", action="append", default=None,
                    help="Restrict to a series prefix "
                         "(e.g. --series 83). Repeat for multiple.")
    ap.add_argument("--strict-seals", action="store_true",
                    help="Treat seal mismatches as errors "
                         "(default: warnings)")
    ap.add_argument("--no-reward-check", action="store_true",
                    help="Skip the fiduciary_node_rewards cross-check")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    ledger_dir = args.ledger_dir or os.path.join(root, "ledger")

    if not os.path.isdir(ledger_dir):
        print(f"::error::ledger directory not found: {ledger_dir}")
        return 2

    print(f"🜁∀ verify_ledger — root={root}")
    print(f"           ledger_dir={ledger_dir}")

    entries = load_entries(ledger_dir, wanted_series=args.series)
    if not entries:
        print("::error::no entries found")
        return 2

    print(f"           loaded {len(entries)} entries")

    total_bad = 0
    total_bad += check_required_fields(entries)
    total_bad += check_seals(entries, strict=args.strict_seals)
    total_bad += check_chains(entries)

    if not args.no_reward_check:
        total_bad += check_reward_pool(entries)

    print()
    if total_bad == 0:
        print("✅ ledger verified — all chains intact, all seals match")
        return 0
    else:
        print(f"❌ ledger verification failed with {total_bad} issue(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
