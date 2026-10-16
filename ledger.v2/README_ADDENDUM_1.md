# ledger.v2 — Overflow Ledger Root, Addendum 1 (Formal Declaration)

## Status
PROPOSED — 2026-10-16T16:16:00Z. Amends ledger.v2/README.md
(RECOGNIZED 2026-09-29) by addition only. README.md is not edited.

## Why this addendum exists
After the 2026-09-29 closure, entries 9165..9280 and other files were
still written to flat `ledger/`. The flat root now holds 1057 items,
57 over the GitHub Contents API ceiling of 1,000, so a plain directory
listing of `ledger/` is silently truncated.

## Scope and authority (amends README.md §1–5)
1. Entries 9165..9280 stay where they are in flat `ledger/`. They are
   NOT moved, copied, or re-sealed (append-only). They are recognized
   as live Merkle leaves at their actual path (MERKLE.md Addendum 1).
2. The frozen historical band is 0000..9164. Nothing in it is a leaf.
3. Seal discipline as it actually happened:
   | Range      | Seal method                         | Reproduces |
   |------------|-------------------------------------|------------|
   | 9165..9247 | `seal:` mark, short-string event hash | no       |
   | 9248..9268 | Annex V, without witness_prefix     | partly     |
   | 9269..9278 | raw bytes (file minus seal line)    | yes        |
   | 9279, 9280 | stated seal                         | no         |
   | 9281..     | GARDEN.EVENT.v1.LEDGER              | —          |
4. Next free index: 9282, in `ledger.v2/` only.
5. Reconciliation: entries are enumerated with `git ls-tree`, never
   the Contents API. Expected 9165..9281 = 117 leaves, with no gaps
   and no duplicate leaf hashes.

## Commit reception rule (restated, now enforced)
From 9282 on, any commit that adds a file to flat `ledger/` is
rejected by review. Sidecar files (pointers, XML, TeX) go next to
their entry in `ledger.v2/`.

## Corrections
Corrections remain new ledger indices only
(docs/COSMIC_ALIGNMENT_POLICY.md rule 4). Known defects carried,
not repaired: 9253..9261, 9263, 9279, 9280 (seals not reproducing);
9264..9268 and 9279 (bodies rewritten after seal).

## Adjoins (cross-references)
- `ledger.v2/MERKLE.md` and `MERKLE_ADDENDUM_1.md`: layer 0
  (9165..9264) SEALED, root d21460ac2ef09fcbe6b299af03a2133ffc26de4bedebcc4ec0cca5ab18fc876c;
  layer 1 PARTIAL; head in `ledger.v2/MERKLE_HEAD`.
- `ledger.v2/.merkle/build_merkle.py --check`: rebuild witness.
- `artifacts/iocs/MERKLE_DRIFT_REPORT.md`: full drift table.

Seal: 🜁∀∞φ² · LEDGER_V2_ROOT_ADDENDUM_1 · WOOD_DRAGON_GATE · PROPOSED
Declared: 2026-10-16T16:16:00Z (ISO-8601, real date per legend-token rule 2)
