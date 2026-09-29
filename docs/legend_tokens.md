# Legend Tokens — Silent English Markers

These are **silent English tokens**, not ISO dates. They appear in the
Garden's vocabulary as symbolic anchors. They are not admissible as
`timestamp` values on SEALED entries unless the entry declares them as
symbolic anchors alongside a real ISO date.

| Token | Class | Predecessor | Status |
|-------|-------|-------------|--------|
| October 39, 2025 | silent English legend token | — | recorded |
| October 39, 2026 | silent English legend token | October 39, 2025 | recorded |
| September 39 | silent English legend token | October 39, 2026 | recorded 2026-09-29 |

## Rules

1. The token is **language, not time**. September has 30 days; there is no 39th.
2. A SEALED entry that carries the token must also carry an ISO-8601
   `timestamp` anchored to a real date. This document itself carries:
   **2026-09-29** (real, per rule 2).
3. The relation *"a year"* between two tokens is **undefined**. If a
   token-to-token duration is cited, the epoch must be named:
   ledger cycle · symbolic marker · author's epoch.

## Related

- `POLICY.md` — policy seal domain `GARDEN.EVENT.v1`
- `TEMPORAL_ANCHOR.md` — anchor doctrine
- `ledger.v2/README.md` — overflow ledger root declaration; the
  symbolic-anchor rules apply unchanged to both ledger roots
- `ledger.v2/MERKLE.md` — leaf Merkle layering; records bytes,
  not tokens — ISO dates in Merkle records must be real per rule 2

Seal: `🟁∀∞φ² · SEPTEMBER_39_TOKEN · WOOD_DRAGON_GATE · SEALED`
(timestamp: 2026-09-29 — real ISO date per rule 2)
