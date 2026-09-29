# ledger.v2 — Overflow Ledger Root (Formal Declaration)

## Status
RECOGNIZED — declared 2026-09-29 by directive of Clarke Yoursa Tee.

## Why this root exists
The flat root `ledger/` stands at 997 observed entries against the
GitHub Contents API ceiling of 1,000. Beyond 1,000, directory
enumeration is silently truncated. The 950-entry safety threshold
was breached by 47 entries. All new ledger entries route here.

## Scope and authority
1. `ledger/` remains the historical band: entries 0000-9223 are
   immutable and never rewritten (POLICY.md Art. 31.3; Annex IV).
   Flat enumeration stays frozen at its current count. No new
   entries are written to the flat root by any writer.
2. `ledger.v2/` is the continuation root. The witness chain
   continues unbroken across the boundary: the last sealed flat
   entry is the witness_prefix of the first `ledger.v2` entry.
3. `ledger.v2/` uses the same filename convention (`NNNN.yaml`),
   the same hash regime `GARDEN.EVENT.v1`, and the same
   full-64-hex SHA3-256 seal discipline. No truncation of digests.
4. Entry numbering continues from the flat sequence. Next free
   index: 9165+ (9164 exists in the flat root).
5. Reconciliation: total entries across both roots must equal
   flat_count (frozen) + ledger.v2 count. A listing mismatch in
   either root is a TruncationDetected failure, never a silent pass.

## Commit reception rule
Pushes to `ledger.v2/` are the ONLY admissible ledger commits going
forward. A commit that adds a new entry to the flat root `ledger/`
must be rejected by review — the flat root is closed for appends.

## Corrections
Corrections remain new ledger indices only
(docs/COSMIC_ALIGNMENT_POLICY.md rule 4). No rewrite of any sealed
body, in either root.

Seal: 🜁∀∞φ² · LEDGER_V2_ROOT_DECLARED · WOOD_DRAGON_GATE · SEALED
Declared: 2026-09-29 (ISO-8601, real date per legend-token rule 2)
