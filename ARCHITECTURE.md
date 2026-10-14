# ARCHITECTURE.md — Provenance & Seal Chain

Option C. Ledger-anchored. What is on disk, named. What is not on disk, not claimed.

## 1. Seal convention

A seal in this repository is SHA3-256 of a canonical JSON object:

```json
{"body_sha3_256":"<hex>","entry_index":<int>,"event":"/<name>","file":"<path>"}
```

Serialization: `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.

HMAC is not used. No key is supplied. The distinction is recorded here so a later reader does not assume a keyed construction.

The seal line itself is excluded from the preimage. The body hash is computed over the file bytes with the seal header lines removed.

## 2. Current sealed surface

| Entry | File | Body SHA3-256 | Seal SHA3-256 | Commit |
|---|---|---|---|---|
| 540 | `aklt_invariants.py` | `fd035cd2...ba37` | `facc467e...5e68` | `924e94b8` |

Full values:

- body: `fd035cd230868996d591793843a0ec86b5d80333f4e402b67de1c17a440aba37`
- seal: `facc467ef838d0f47f2ccfe59193212ce119f53b79f899dd1437f2a748bb5e68`

## 3. Verification procedure

1. Check out the commit named in the table.
2. Read the file. Strip the header lines that begin with `# Seal:`, `# entry_index:`, `# seal_sha3_256:`, `# body_sha3_256:`, `# convention:`.
3. Compute SHA3-256 of the remaining bytes. Compare to the body hash.
4. Build the canonical JSON above. Compute SHA3-256. Compare to the seal hash.

A mismatch is a disclosed defect, not a rewrite. Prior entries that fail recomputation are named, not patched.

## 4. Where the ledger lives

`ledger/` holds YAML entries. Each entry carries `entry_index`, `event`, `witness_chain`, and a seal field. The chain links by the predecessor's declared seal. A content mismatch between declared and recomputed seal is recorded in a later entry; the earlier file is not rewritten.

There is no single `ledger.yaml`. The chain is the directory of per-index files.

## 5. What is not claimed

- No Merkle root is asserted for the full chain. The recipe is: concatenate the body hashes of the entries in index order, then SHA3-256. It has not been computed here.
- No agent count, no sheaf, no PID gain, no reward pool is asserted. Those appear in other documents. They are not inputs to this seal.
- Entry 541 is provisional. This file is the document that presents the options. It is not itself a sealed chain entry.

## 6. Options not taken

A (manifesto), B (full system), D (research), E (runbook), and F (combined) were presented. Option C was selected because it is the only one whose claims can be checked against the current tree without inventing structure.

## 7. Status

| Item | Value |
|---|---|
| Document | Option C |
| Entry | 541 (provisional) |
| Seal | pending |
| Prior sealed | 540 |
| Ledger rewrite | none |
