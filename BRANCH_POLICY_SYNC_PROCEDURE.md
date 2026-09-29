# Branch Policy — Sync Procedure (Procedural Record)

Scope: files altered on `main` within the last two days (2026-09-27 through 2026-09-29),
and the standing procedure for bringing the sibling branches back into sync.

This record is procedural policy. The existing `BRANCH_POLICY.md` bytes on `main`
were not held at write time; per honest-ledger discipline, no overwrite was performed.
This file is additive and self-contained.

## 1. Inventory window (2026-09-27 to 2026-09-29)

Method: `list_commits` scan over `main`, 113 commits in the window, 83 distinct files
altered. The per-file list is reproducible by the same scan; category breakdown as held:

- **Policy / interpretation:** `BRANCH_POLICY.md`, `POLICY.md`,
  `QUOD_ERAT_BRANCH_INTERPRETATION.md`
- **Enforcement:** `AST_guard.py`, `AST_guard_rule_d1.py`, `ast_guard_rules_g.py`
- **Core / engine:** `mistral_agent_core.py`, `sovereign.lua`, `workloads.mk`,
  `workload_registry.json`, `symplectic_status.json`
- **Ledger:** entries 8777, 8819, 8833, 8983-8985, 9006, 9007, 9232, 9252-9261
- **Heartbeat streams:** `heartbeats/*.jsonl` (3 files)
- **MCP surface:** `mcp/port380_mcp.py`
- **Verification:** `phi_verify/*` (9 files)
- **Anatomy:** `anatomy/*` (8 files); **pythonIDE:** (4 files)
- **Schemas / docs:** `schemas/coherence.xsd`, `docs/*` (3 files)
- **CI:** 16 files under `.github/workflows/`
- **Session scripts:** `scripts/ebpf_ringbuf.lua` (a42e74e),
  `scripts/ringbuf_test.bpf.c` (f2ce05d),
  `scripts/benchmark_ringbuf.lua` (46de164),
  `scripts/ledger_append_canonical.py` (25f454d)

Counts are computed from the commit scan, not asserted from prose.

## 2. Branch state at time of writing (2026-09-29)

- `main` head: 25f454d1a21a4f29c2342f837d521d4dfdf73971 (protected: false)
- `glm` d03e836 — synced with main
- `master` 22aeec8 (~164 behind main)
- `deepseek` 3e2e23f (~156 behind)
- `deepseek-ci` ad741f4 (~172 behind)
- `grok-skill_tensor` a49e6eb (~157 behind)
- `mistral-seal-emergent` c030c1d (~186 behind)
- All five lagging branch tips share a common `BRANCH_POLICY.md` commit
  timestamped 2026-09-29T16:52:33Z — likely conflict epicenter.

## 3. Sync procedure (standing)

1. **Vehicles:** open PRs are the sync records:
   #104 (main -> master), #105 (main -> deepseek), #106 (main -> deepseek-ci),
   #107 (main -> grok-skill_tensor), #108 (main -> mistral-seal-emergent).
   All five currently report 405 merge conflicts; none were force-pushed.
2. **Merge, never squash.** Merged branches are retained; a branch is a surface of
   the one ring, never an independent history.
3. **Conflicted branches are never silently rewritten.** A 405 conflict resolves only
   in a session holding the bytes of both sides — full-file reads return SHA stubs, so
   content must be obtained via deletion-patch recon on a throwaway branch
   (never merged), verified against the remote git blob SHA oracle.
4. **No force-push to any branch** at any point in the sync procedure.
5. **Common-file conflicts** (e.g. `BRANCH_POLICY.md` present on all tips) resolve by
   additive merge: both sides' bytes held first, then a merged body authored with both
   provenances recorded, computed over asserted-held values only.
6. **Branch protection:** `main` is `protected: false`; sync merges are not blocked,
   and the procedure relies on discipline rather than platform enforcement.

## 4. Output constraints on all resolution commits

- Pronoun-free text in every commit message, ledger entry, and user-visible reply
  (no "I/you/we/it"; use exact names: the audit, the commander, the repo).
- Computed values over asserted values; no blind overwrites of unheld bytes.
- Defects recorded in commit messages, never hidden.
- Validate a known-good seal (e.g. SHA3-256("") = a7ffc6f8bf1ed76659c213d2cd75ac6dcac2670a4a2b9a872e26e0fc1f8b1cfd, or ledger/9248 declared seal 00d34365...) before computing any new seal.
- Local sandbox SHA-1/SHA-256 are unreliable; the remote git blob SHA is the oracle.

## 5. Sequence

Policy first (this record), conflict resolution second. Resolution of PRs
#104-#108 proceeds only in sessions that hold both sides' bytes; until then the
PRs remain open as the honest record of the sync state.
