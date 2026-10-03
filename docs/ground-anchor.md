# Ground anchor

Surface: GitHub `AxiomicCoreness/hello_world.py`, branch `main`.
Read: 2026-10-03T19:29Z.
This file records what was checked. It is not a ledger seal.

## Held

- φ = (1 + sqrt(5)) / 2 = 2 cos(π/5).
- φ² = φ + 1. φ³ = 2φ + 1. φ⁴ = 3φ + 2.
- ε = φ⁻¹⁴¹⁸ = 4.524036764254231e-297 in binary64. The value 1.04e-300 stays retracted.
- Blob `d13dea749b7cd29d081d41e2d14c8267bbaebeeb` unchanged.
- Body seal `cf5d38f84f9a40792bb6ad4f424ea01679edf764896278402e1b35b558d276ef` unchanged.
- Lindblad file hash `88d1e766bc6f5f1b72ef3357a8e70c0c57e488f3abbb986c56706f06de733e2a`: L_k = 0 for every k, so dρ/dt = -i[H, ρ].
- Frequency ladder f_n = 6.49 · φⁿ matches the printed harmonics through n = 14. f_7 = 188.434 Hz.

## CI

- `httpx==0.27.2` is on the two TestClient install lines. Commit `b7d83ccb82e487f002d79dbf2acdccf9bec75dd7`. Run 37147525023 success.
- Stack CI re-run 37147625917 success. The stale `from __future__` failure is not the current tree.
- Parity dispatcher commit `f5a23809c2ea834f862c580a1e4703f601052f61`: one file per tick, index modulo 55. Not yet verified by a run.

## Not held

- `ledger/8128.yaml` is not on main. The 32-hex strings in the 8128 block are labels, not SHA3-256.
- Index 9265 is `ledger/9265.yaml`. Seal `a7580ccb6624d666e84fb9f6a2ba471c2be22541f2d6fae78c5aa448399a6177`. The earlier `0c90d96a…` line was stale. No 9265 stub. `ledger/9266.yaml` is not on main. The entry's own `prior_recompute.match` for 9264 is false.
- Service and CronJob are not applied. No kubeconfig. No securityContext.
- 3I/ATLAS is not a deployment target of this repo.

## Open check

```bash
gh workflow run workflow-parity.yml --repo AxiomicCoreness/hello_world.py --ref main -f slot=0
```

Pass condition: the log prints `dispatch hypersurface.yml` and no second `dispatch`.
