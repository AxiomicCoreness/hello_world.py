# Section V — Cross-Branch Consolidation

Documentation draft, ledger genesis anchor 9195. Append-only.
No fabricated hashes. No rewrite of prior entries.

## §V.1 Purpose

Defines consolidation contract: same program across branches by digest.
Does NOT merge branches. Defines invariants a merge would preserve.

## §V.2 Branches in scope

main (and any other branches that exist). Note: repository may be main-only;
absent branches are N/A in the status table.

## §V.3 Consolidation invariants

- Ledger continuity for 9195 segment if present
- docs/frb_bridge_tolerance.md present with binary pass/fail
- All k8s/section-iv/* seven files present
- No 0.0.0.0; mcp.garden/filled: "false"; garden.genesis_ledger: "9195"
- pythonIDE/argo_sink.py stub: no socket at import, no subprocess/eval

## §V.4 Drift detection

drift(B1,B2) = { f : sha3_256(B1/f) ≠ sha3_256(B2/f) } over program file set.

## §V.5 Program file set

ledger/9195.yaml, docs/section_iii_accrued.md, docs/frb_bridge_tolerance.md,
k8s/section-iv/* (7 files), pythonIDE/argo_sink.py

## §V.10 Not claimed

Does not claim any branch currently satisfies invariants or that a merge is desirable.

## Doctrine footer

Origin — Clarke Yoursa Tee · Consolidation — same file, same digest ·
Bridge — not identity · Section V — contract only.
