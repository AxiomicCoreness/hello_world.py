# Apply note — local checkouts only

--apply ran on the local checkouts of both branches. The rewritten tree was not pushed. Main was not touched. Ledger index 9266 was not taken.

| Check | Value |
|---|---|
| files rewritten | 79 |
| insertions / deletions | 192 / 192 |
| diff bytes | 68375 |
| external sha256sum | `de8f237656db6a433fe0d417fcdb9b61d0c01226e24ae78864cdd0b24c5dbab4` |
| python sha256 | same, match true |
| hash % 9266 | 8636 |
| hash % 997 | 739 |

Both branches produced the same diff hash. A second dry-run still reported 79 files with residual tokens, so the apply is not idempotent yet. Sealed-history ruling is still open.
