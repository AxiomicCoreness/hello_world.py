# Reading `ledger/` and `ledger.v2/` in unison

Both folders are **append-only**. Nothing here edits, renames or removes a ledger file.

| Piece | What it does |
|---|---|
| `tools/ledger_seal.py` | The one seal core. Regimes **A** (canonical JSON, `ensure_ascii=False`), **A_ASCII** (old `scripts/verify_ledger.py` form), **B** (`GARDEN.EVENT.v1[.LEDGER]`, `.LEDGER` from 9281), **S** (`seal_sha3_256` explicit preimage). All three verifiers call it. |
| `tools/ledger_index.py` | Reads both folders, writes `ledger_index.jsonl` sorted by `(entry_index, folder, path)`, appends to `ledger.chain.jsonl`. `--check` fails if either is stale or the chain breaks. |
| `ledger_index.jsonl` | One row per YAML document, unified schema below. Regenerated in full. |
| `ledger.chain.jsonl` | `{seq, entry_index, path, sha256, prev_hash}`; `sha256` is over the file bytes, `prev_hash` is the previous line's `sha256` (genesis = 64 zeros). Only ever appended; a changed or missing file breaks it. |
| `.github/workflows/ledger-unison.yml` | Runs `--check` and the tests on every push/PR. No skips, no continue-on-error. |

## Unified row schema

`entry_index`, `folder`, `path`, `doc`, `event`, `timestamp` (ISO-8601 UTC, extracted from forms like
`ETERNAL_NOW_ANCHORED_TO_2026-07-30T00:00:00Z`, else `null` + flag), `status`, `commander`,
`null_ban` (from `null_ban` / `nullify_ban` / `null_ban_sigma` / `nullban`), `witness_chain`, `seal`,
`seal_status` (`verified` | `unverified` | `no_declared_digest`), `seal_regimes`, `field_aliases`
(which old name was used), `flags`, and `raw` (all original fields, untouched).

## Flags

`parse_error`, `empty_file`, `non_mapping_document`, `missing_entry_index`, `index_filename_mismatch`,
`timestamp_unparsed`, `outlier_index` (>99999, e.g. 510510), `duplicate_index`,
`duplicate_index_cross_folder` (v1/v2 mirror), `seal_unverified`, `seal_sha3_256_mismatch`,
`seal_method_mismatch` (>=9281 but not Regime B).

An entry whose seal no regime reproduces is **unverified**, never a pass.

## Adding an entry

1. Add the new `ledger/NNNN.yaml` (or `ledger.v2/NNNN.yml`).
2. `python tools/ledger_index.py`
3. Commit the entry together with `ledger_index.jsonl` and `ledger.chain.jsonl`.
