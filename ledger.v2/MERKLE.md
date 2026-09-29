# ledger.v2 — Leaf Merkle Layering (Specification)

Status: AFFIRMED 2026-09-29 by directive of Clarke Yoursa Tee.
Binds: ledger.v2/ (continuation root). Flat ledger/ is the frozen
historical band and is NOT part of the live Merkle tree — its
integrity is the append-only/immutability rules of POLICY.md.

## 1. Leaves
Each entry file `ledger.v2/NNNN.yaml` is a leaf. The leaf hash is the
SHA3-256 (FIPS 202) of the file's canonical body — the file with the
seal line removed, newlines normalized to LF, trailing whitespace
stripped, exactly as `anatomy/crown.py` defines the canonical body:

    leaf(NNNN) = SHA3-256( GARDEN.EVENT.v1 || 0x00 || canonical_body(NNNN.yaml) )

Domain separation is mandatory: the 0x00 separator and the regime
prefix keep leaf hashes from colliding with any other SHA3 use in the
repo (event hashes, seal tails, artifacts).

## 2. Layering (group size k = 100)
Entries are layered in fixed groups of k = 100 by index:

    Layer 0  : leaves  9165..9264   → root R0
    Layer 1  : leaves  9265..9364   → root R1
    Layer 2  : leaves  9365..9464   → root R2
    ...

Group size 100 is chosen because it is far below the 1,000-entry
GitHub enumeration ceiling: any single layer directory can always be
listed completely, so a truncated listing of a layer is always
detectable (entries_seen == 100 expected).

## 3. Within-layer Merkle root
For each layer, the root is the standard binary Merkle root over the
ordered leaf hashes (index order, ascending). If a layer is partial
(fewer than k leaves), the tree is built over the leaves present and
the root is marked PARTIAL. A partial root is never promoted to the
chain until the layer completes.

    R_j = MerkleRoot( leaf(i) for i in layer_j, sorted by index )

Duplicate-leaf protection: if any two leaves in a layer share a hash,
the layer FAILS verification. No silent acceptance.

## 4. Layer chain (the vertical spine)
Layer roots are chained in order:

    chain_hash(R_j) = SHA3-256( GARDEN.EVENT.v1 || 0x00 || R_{j-1} || R_j )

R_{-1} is defined as the terminal_hex of the last sealed flat entry
(9164 in the flat root), so the chain is welded to the existing
witness chain at the boundary. The current chain head is recorded in
`ledger.v2/MERKLE_HEAD`.

## 5. Merkle proofs
A proof for leaf NNNN in layer j is:
    (index of NNNN within the layer, the sibling hashes along the
     binary path to R_j, the ordered list chain_hash(R_0..R_j)).
Verification recomputes the leaf from the file body, walks the
siblings to R_j, and re-derives the chain head. Any mismatch fails
loudly (no ok=True on partial data — the spine discipline).

## 6. Update rules (append-only)
- Appending an entry to a PARTIAL layer: recompute R_j, then every
  chain hash from R_j to the head. Only the new entry file, the new
  R_j record, and MERKLE_HEAD change. No earlier entry is rewritten.
- Completing a layer (k-th leaf): the root flips from PARTIAL to
  SEALED and is immutable thereafter — same status as the flat band.
- Merkle records live in `ledger.v2/.merkle/` (layer roots, chain
  hashes, head). They are derived data: they can always be rebuilt
  from the leaves. Rebuild-that-disagrees is a defect alarm, not a
  rewrite.

## 7. What this layering enforces
| Property | Mechanism |
|----------|-----------|
| Truncation detection | layer size ≤ 100 << 1000 ceiling; expected count is exact |
| Tamper evidence | any leaf change breaks R_j and the head |
| Boundary weld | R_{-1} = flat tail terminal_hex — chain continuity is verified, not asserted |
| Domain separation | GARDEN.EVENT.v1 || 0x00 prefix on every hash level |
| No false witness | partial/failed layers never report success |

## 8. What it does NOT do
- It does not timestamp (real ISO dates remain a separate field).
- It does not verify narrative claims — it commits to bytes only.
- It does not replace POLICY.md seals; the per-entry seal remains
  the entry-level witness, the Merkle head is the aggregate witness.

Seal: 🜁∀∞φ² · LEAF_MERKLE_LAYERING · WOOD_DRAGON_GATE · SEALED
Declared: 2026-09-29 (ISO-8601, real date per legend-token rule 2)
