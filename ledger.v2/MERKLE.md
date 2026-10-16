# ledger.v2 — Leaf Merkle Layering, Addendum 1 (Specification)

Status: ACTIVE 2026-10-16T17:26:00Z (continuation unpaused). Amends ledger.v2/MERKLE.md
(AFFIRMED 2026-09-29) by addition only. Original MERKLE.md body is not rewritten.
Binds: ledger.v2/ (continuation root). Flat ledger/ remains the frozen
historical band and is NOT part of the live Merkle tree.

## 1. Leaves (clarifies MERKLE.md §1)
Only files at `ledger.v2/NNNN.yaml` are leaves. The leaf formula is
unchanged:

    leaf(NNNN) = SHA3-256( GARDEN.EVENT.v1 || 0x00 || canonical_body(NNNN.yaml) )

The leaf hash is independent of the per-entry seal method. A seal
that does not reproduce is recorded as `seal_reproduces: false` and
does not alter the leaf.

## 2. Boundary drift (observed 2026-10-16T16:15:00Z)
Entries 9165..9280 were written to flat `ledger/` after the
2026-09-29 closure, contrary to README.md "Commit reception rule".
They are NOT moved, copied, or re-sealed (append-only). They are
boundary objects, not leaves:
- Layer 0 (9165..9264) has 0 leaves → status EMPTY, never SEALED.
- Layer 1 (9265..9364) has leaves 9281, 9282 → status PARTIAL, continuation UNPAUSED.
- Missing indices are reported, never assumed.

R_{-1} stays as MERKLE.md §4 defines it: terminal_hex of ledger/9164.yaml.

## 3. Per-entry seal methods (for the record, not for leaves)
| Range        | Seal method                              | Domain prefix |
|--------------|------------------------------------------|---------------|
| ..9268       | Annex V (canonical JSON of parsed YAML)  | none          |
| 9269..9280   | raw bytes (file minus seal line)         | none          |
| 9281..       | GARDEN.EVENT.v1.LEDGER                   | yes           |

## 4. Pointer pinning (new rule, from 9282)
An entry that points to a file (`latex:`, `xml:`, `script:`) MUST
also carry `<field>_sha3_256`, the file's SHA3-256 at seal time.
Reason: ledger/cdp_status_fallback.tex was changed (commit 146c78d1,
2026-10-08T01:37:30Z) after 9269 referenced it (2026-10-08T01:13:34Z).

## 5. Records (implements MERKLE.md §6)
    ledger.v2/.merkle/build_merkle.py   builder; --check exits nonzero on mismatch
    ledger.v2/.merkle/leaves.json       index, path, leaf, seal, seal_reproduces
    ledger.v2/.merkle/layer_0000.json   R0, status
    ledger.v2/.merkle/layer_0001.json   R1, status
    ledger.v2/.merkle/chain.json        chain_hash(R_j), SEALED layers only
    ledger.v2/MERKLE_HEAD               head, or R_{-1} while no layer is SEALED

## 6. Known defects carried, not repaired
- Seals not reproducing: 9253..9261, 9263, 9279
- Bodies rewritten after seal: 9264..9268 (2026-10-04), 9279 (2026-10-15T13:56:27Z)
- witness_prefix added after seal: 0340..0439, 9248..9268 (2026-10-07)
- 9276 source_seal is 60 hex, not 64 (from 0353, CONTAMINATED band)
- Timestamps 9274..9278 carry local time (−04:00) labelled Z (+4h offset)
Corrections are new indices only (README.md "Corrections").

## 7. What this addendum does NOT do
- It does not admit flat entries into the live tree.
- It does not repair any sealed body.
- It does not verify narrative claims; it commits to bytes only.

## 8. Continuation status (2026-10-16T17:26:00Z)
Ledger entry continuation unpaused. Next free index: 9283.
Layer 1 remains PARTIAL until 9364. Appends continue under GARDEN.EVENT.v1.LEDGER.

Seal: 🜁∀∞φ² · LEAF_MERKLE_LAYERING_ADDENDUM_1 · WOOD_DRAGON_GATE · ACTIVE
Declared: 2026-10-16T16:15:00Z (ISO-8601, real date per legend-token rule 2)
Unpaused: 2026-10-16T17:26:00Z
