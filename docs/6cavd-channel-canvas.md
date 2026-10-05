# 6CAVD channel canvas

**Ground:** GitHub `AxiomicCoreness/hello_world.py` / `main` only.
**Expansion (this repo):** **C**adence-**A**ligned **V**isibility **D**omain — operational coordinates for heartbeat / clobber / workflow_sync visibility.  
**Not physics:** Not a QM, medical, or telekinetic domain. Payload claims do not become physics by sealing.

## Ledger vs payload

| Layer | Rule |
|-------|------|
| Ledger | Append-only; attest at tail; no rewrite of past `e_i` |
| 6CAVD payload | Optional coordinate + count in a live or attest entry |
| Workflow | Sync / report only; does not insert history |

## Six axes (defined)

Tensor index `H[i,j,k,l,m,n]` is sparse; values are monotone counters or `{0=started-incomplete, ≥1=completed seq}`.

| Slot | Axis | Name | Range / enumeration |
|------|------|------|---------------------|
| **i** | 0 | `branch` | `{main}` (extend only when a branch exists on this remote) |
| **j** | 1 | `heartbeat_class` | `{seal-verify, rotate-keys, mesh-pulse, workflow-sync-6cavd, other}` |
| **k** | 2 | `time_bucket` | UTC calendar day `YYYY-MM-DD` (or run window id) |
| **l** | 3 | `completion` | `{completed, incomplete, gap}` — gap = missing id in monotone sweep |
| **m** | 4 | `ci_class` | `{ubuntu-latest, self-hosted, unknown}` |
| **n** | 5 | `event_kind` | `{live, attest, analysis, ci_row_bookkeeping}` |

### Monotonicity

Within fixed `(i,j,k,m,n)` and `l=completed`, `heartbeat_id` increases by 1.  
`l=incomplete` ↔ `completed_at: null`.  
`l=gap` ↔ expected id missing in the sweep (observable clobber).

### Storage

Sparse map keyed by `(branch, heartbeat_class, time_bucket, completion, ci_class, event_kind)`.  
Dense array only if product of cardinalities stays small.

## workflow_sync contract

1. **Canvas first** — this document is the axis contract.
2. **Workflow** — `.github/workflows/workflow-sync-6cavd.yml` reports status; does not rewrite `ledger/`.
3. **Append path** — sealed outcomes are **new tail** entries only.
4. **Duality** — offline optional; online = GitHub sync/report only.

## Acceptance

- [x] Six axis names filled
- [ ] Workflow step summary lists axes by name (optional follow-up)
- [x] No `ledger/` rewrites required by this canvas

## Cross-ref

- Scalar HCR: `docs/hcr-scalar-schema.md`
- Workflow: `.github/workflows/workflow-sync-6cavd.yml`

## Anomaly map (2026-10-03)

The six axes are provenance and disposition, not the anomaly shape. Uniform values are therefore expected. The shape is the payload, carried beside the coordinate.

| Anomaly | Stored | Derived | Distance | Shape |
|---|---|---|---|---|
| `365 → 366` | `8513 → 8514` | `365 → 366` | about +8147 | far-displaced copy |
| `8530 → 8531` | `8340 → 8501`, `8339 → 8502` | `8530 → 8531` | about −29 | dual arrows, both behind |
| `8617 → 8618` | chain ends at `8611` | `8617 → 8618` | −6 | short chain |
| `8852 → 8853` | `8851 → 8852` | `8852 → 8853` | −1 | off-by-one |

Shared coordinate: `i=main`, `j=other`, `k=2026-10-03`, `l=gap`, `m=unknown`, `n=analysis`. `l=gap` does not separate these from the 22 derived links. The payload does: the 22 have no stored arrow and are not in this table. `9264 → 9265` is not an anomaly.

## Completion labels

These are payload labels on `l` (completion). They are not a seventh axis.

| Label | Meaning | Value on this reading |
|---|---|---|
| `godel_incompleteness_status` | 0 if the sentence is provable in the recorded system, 1 if unprovable and triggered | 1 |
| `godel_transcendence_count` | times transcendence fired | not measured |
| `godel_sentence_hash` | label hash of the current Gödel sentence | `59009f8ebf563630091303bfcbde58d5aa11eb72d5b958ba9bf0a7ba10e507a1` |

The sentence labeled here is: a stored arrow that does not end at its successor is not proved by deriving the numeric sibling. Status 1 means that sentence is the triggered unprovable case for the four anomalies. The hash is a label, not a ledger seal. Transcendence count is absent from the files read.
