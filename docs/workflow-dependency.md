# Workflow dependency

The legend anchor is a position. It is not a differential equation and it is not a dispatcher.

```text
cadence_quadratic.py
        |
        v
test_slot_boundary.py          traffic_cop.py
                               |
                               v
                     parity_gitcode_atomgit.py
                               |
                               v
legend_anchor.py ----> dual_interaction_layout.py
        |                        |
        | label only             | read only
        v                        v
eridanus_flow.py          GitHub pane | GitCode pane
(not written)             no dispatch
```

| Edge | Kind | Rule |
|---|---|---|
| cadence → slot test | test | boundary stays between slot 10 and 11 |
| traffic cop → parity | table | one 55-slot source |
| parity → dual layout | label | names the workflow, does not run it |
| legend anchor → dual layout | position | token is not a date |
| legend anchor → Eridanus flow | label only | `t` may cite the index; it may not date the token |
| parity → eridanus-dual-smoke | slot name | smoke lane is read-only |
| smoke → ledger | forbidden | no ledger growth from the smoke workflow |

The DE family is not chosen. Lagrangian, three-term Hamiltonian, and Eridanus flow stay out of `scripts/legend_anchor.py`.
