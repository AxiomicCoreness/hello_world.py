# MATH.md — codespace-phi-draft

Signitorial: Clarke Yoursa Tee

Review-branch draft. Does not rewrite `k8s/codespace/MATH.md` (ledger 9157).
Source of truth: `celestial/phi_constants.py` (computed). MCP unfilled.
Dual ASGI `127.0.0.1:8024`.

## φ-power ladder (computed)

| Symbol | Value | Use |
| --- | --- | --- |
| φ | 1.618033988749895 | Base ratio |
| φ² | 2.618033988749895 | CPU request floor = 2 |
| φ⁴ | 6.854101966249686 | Memory request floor = 6 |
| φ⁵ | 11.090169943749475 | CPU limit floor = 11 |
| φ⁶ | 17.944271909999160 | Memory/pods floor = **17** (not 18, not 13) |
| φ⁸ | 46.978713763747790 | Service floor = **46** if derived; paste used 8 (D21) |
| φ⁻¹ | 0.618033988749895 | Ring modulation |
| φ⁻⁷⁰⁹ | 6.726096017939553e-149 | Entropy-adjacent |
| φ⁻¹⁰⁰⁰ | 1.028868213399699e-209 | **D19 fix** — was mislabelled 4.524e-297 |
| φ⁻¹⁴¹⁸ | 4.524036764254231e-297 | Actual identity of the ghost literal |

## What this draft does not do

- Does not rewrite sealed `ledger/9156.yaml`–`9158.yaml`
- Does not overwrite `k8s/codespace/`
- Does not expose MCP port 380
- Does not require `garden-secret`
- Does not bind `0.0.0.0`
- Does not claim 15-nines coherence
