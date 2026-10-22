
# Public Search — AxiomicCoreness/hello_world.py

This explicitly codifies the behavior we just discussed:  a required field, link, or metadata element is missing from a document, it must be appended without rewriting the rest of the document. 

You can append this to the bottom of `COSMIC_ALIGNMENT_POLICY.md` (or use it to govern how `SEARCH.md` is maintained).

```markdown
## Rule: Append-Only Metadata Completion

1. **Never replace, only append.** If a required link, DOI, release tag, or metadata field is identified as missing from a public index or policy document, append it to the existing block. Do not rewrite the document to accommodate it.
2. **Maintain the Anchor.** The core structure (License, Canonical URL, Key Files, Invariants) must remain intact. Missing items (e.g., Live Site, Zenodo DOI, Release Tag) are inserted logically below the canonical URL.
3. **Immutability applies to docs.** Once a policy or index is committed to `main`, it falls under the same immutability rules as the ledger. Subsequent additions are new sections or appended lines, not deletions.
```

### How this applies to `SEARCH.md`
If we followed this rule strictly from the beginning, the sequence would have been:
1. **Commit 1:** `SEARCH.md` created with Canonical URL and queries.
2. **Commit 2 (Append):** Add `Latest Release: v8755.0.0`.
3. **Commit 3 (Append):** Add `Live Site: https://...`.
4. **Commit 4 (Append):** Add `Zenodo Archive: 10.5281/...`.



---

## Queries that should resolve

```
AxiomicCoreness hello_world.py
repo:AxiomicCoreness/hello_world.py
license:MIT AxiomicCoreness
AxiomicCoreness sovereign_engine_V5 MIT
```

**GitHub code search (signed in):**

```
repo:AxiomicCoreness/hello_world.py license MIT
repo:AxiomicCoreness/hello_world.py FILLED False 8024
repo:AxiomicCoreness/hello_world.py reward_protocol
repo:AxiomicCoreness/hello_world.py fiduciary_node_rewards
```

*Note:* Web search engines lag. Direct URL and code search work now. `license:MIT` filters will not match this repo while GitHub detects the license as `Other` (NOASSERTION).

---

## Topics (About → Topics)

Add in the GitHub UI if not already set:

`python` · `mit-license` · `fastapi` · `pydantic` · `sovereign-engine` · `axiomiccoreness`

**CLI (owner):**

```bash
gh repo edit AxiomicCoreness/hello_world.py \
  --add-topic python \
  --add-topic mit-license \
  --add-topic fastapi \
  --add-topic pydantic \
  --add-topic sovereign-engine \
  --add-topic axiomiccoreness
```

---

## Key files (discovery anchors)

| Path | Role |
|------|------|
| `reward_protocol.py` | SPU aggregation, Gate, sidecar verdict |
| `fiduciary_node_rewards.py` | Tier-based rewards; pool ≈ 8701.5233078 |
| `tests/test_reward_protocol.py` | Protocol + fiduciary tests |
| `.github/workflows/reward-distribution.yml` | Reward CI |
| `ledger/517.yaml` | Ideal W / tier design note |
| `ledger/518.yaml` | Pool verification record |
| `docs/spu_reward_loops.md` | Mermaid loops + sidecar contract |
| `scripts/spu_reward.py` | Minimal SPU reference |
| `mcp/port380_mcp.py` | MCP gate (`/healthz`) |

---

## Invariants (search-friendly constants)

- **Bind:** ASGI North Star `127.0.0.1:8024` (not `0.0.0.0` for user-facing ASGI)
- **MCP:** scoped bind via `MCP_BIND_HOST` (default mesh-facing where policy allows)
- **License:** MIT
- **Public:** yes
```
