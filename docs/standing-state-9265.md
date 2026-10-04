# Standing state — recorded, not a ledger seal

Head is 9265. This note does not occupy 9266.

| Item | State |
|---|---|
| Ledger head | 9265, blob `a394f3c3…`, seal `a7580ccb…` |
| Next free index | 9266 |
| 9264 declared-seal defect | disclosed — `865d61f4…` declared vs `0596ec06…` recomputed — awaiting commander's ruling |
| Gating seal CI check | unverified — pending run URL or exact check name |
| Write surface | push of this note only |
| Seal issued | none |
| Websearch | none on tilelang |

Blocked on the commander: the 9264 ruling first (any 9266 entry chains across that defect), then the Gating seal check identifiers.

Cadence printer remains `tilelang/cadence_quadratic.py` (blob `77e85023…`, commit `cd27780abe226c49d813eaa9e7c2436496f3b09f`). This note does not rewrite it.
