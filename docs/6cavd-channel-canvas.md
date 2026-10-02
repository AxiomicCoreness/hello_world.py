# 6CAVD channel canvas (write-first)

**Ground:** GitHub `AxiomicCoreness/hello_world.py` / `main` only.
**Role:** Design canvas for workflow_sync on the 6CAVD channel.
**Not physics:** This file does not claim QM bounds, forces, or telekinesis.

## Ledger vs payload

| Layer | Rule |
|-------|------|
| Ledger | Append-only; attest at tail; no rewrite of past `e_i` |
| 6CAVD payload | Optional structured data in a live or attest entry |
| Workflow | Sync / report only; does not insert history |

## Six channels (placeholders — names required before tensor schema)

Earlier work left rank-6 CAVD **blocked** until axes are named. Until then:

| Slot | Name | Range / enum | Status |
|------|------|--------------|--------|
| 0 | _TBD_ | _TBD_ | open |
| 1 | _TBD_ | _TBD_ | open |
| 2 | _TBD_ | _TBD_ | open |
| 3 | _TBD_ | _TBD_ | open |
| 4 | _TBD_ | _TBD_ | open |
| 5 | _TBD_ | _TBD_ | open |

Do not invent axis names in CI. Fill this table, then enable tensor checks.

## workflow_sync contract

1. **Canvas first** — this document is the human-readable contract.
2. **Workflow** — `.github/workflows/workflow-sync-6cavd.yml` reads/reports status; does not rewrite `ledger/`.
3. **Append path** — any sealed outcome is a **new tail** entry (live or `kind: attest`), never a mid-chain insert.
4. **Duality** — offline compute optional; online step is sync/report on GitHub only.

## Acceptance (minimal)

- [ ] Six axis names filled above
- [ ] Workflow runs without claiming incomplete tensor schema
- [ ] No `ledger/` rewrites in the workflow
