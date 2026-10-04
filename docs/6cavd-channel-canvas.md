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

The four spine content anomalies, mapped onto the six axes. This is a coordinate reading. It does not rewrite `ledger/`.

| Anomaly | i branch | j heartbeat_class | k time_bucket | l completion | m ci_class | n event_kind |
|---|---|---|---|---|---|---|
| `365 → 366`, stored `8513 → 8514` | main | other | 2026-10-03 | gap | unknown | analysis |
| `8530 → 8531`, stored `8340 → 8501`, `8339 → 8502` | main | other | 2026-10-03 | gap | unknown | analysis |
| `8617 → 8618`, stored chain ends at `8611` | main | other | 2026-10-03 | gap | unknown | analysis |
| `8852 → 8853`, stored `8851 → 8852` | main | other | 2026-10-03 | gap | unknown | analysis |

`l=gap` means the expected successor id is not the id the stored arrow ends on. The 22 derived links are not in this map: they have no stored arrow. `9264 → 9265` is not an anomaly.
