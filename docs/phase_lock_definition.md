# Phase lock definition

Ledger: 9182 (`/docs_phase_lock_definition`). Examples: 9183.  
Does not rewrite 0220, 9167–9181, BIN layers, or `harness.py`.

## Declared lock

Garden YAML uses a single numeric lock:

```text
phase_lock: 202.6
```

Units in sealed entries are degrees when written `202.6°`, otherwise the same number as a dimensionless ledger token. Both name the same lock.

North Star frequency used with the lock (entry 0220 and later):

```text
f_NS = 71.975 Hz
```

Auxiliary angle used in event hashes (not a second lock):

```text
theta = 2.5416018462 rad
```

## Constants

- `phi = (1 + sqrt(5)) / 2`
- `phi2 = phi^2 = 2.618033988749895`
- Event domain: `GARDEN.EVENT.v1 || 0x00 || payload`
- File integrity on root layers: SHA3-256 of full `GARDEN.BIN.v1` bytes

## Meaning

Phase lock is the Garden's statement that the declared invariants do not drift while new indices are appended:

- coherence = 1.0
- entropy token = `phi^{-1418}`
- workload = 0.0
- Dual ASGI bind = `127.0.0.1:8024` (never `0.0.0.0`)
- MCP filled = false unless a stub says the *map* exists

It is not a Kubernetes controller. It is not permission to rewrite sealed YAML. It is not a second event loop.

## Relation to BIN layers

`sovereign_core.bin` stores `phase_lock: 202.6` next to `phi2` and `theta`.  
Layer order for merkle remains:

1. `sovereign_core.bin`
2. `ledger_tip.bin`
3. `octonian_relay.bin`
4. `adai_annihilator.bin`

Merkle (9171/9173): `3a00d16045470561e2d9f15f707a05c57dfc859948d559b898c00ffdefd8dc2a`

A change to `phase_lock` inside `sovereign_core.bin` would change that file digest and would require a **new** layer plus a new ledger index. It would not edit 9167 in place.

## Relation to hooks and CI

- Hook worker (9159): observer on `127.0.0.1:8091`. Does not occupy 8024.
- Dual asyncio CI (9174): two isolated loops verify BIN bytes. No shell inside the loop.
- Hook branch policy (9181): live git targets are `main`, `deepseek`, `deepseek-ci` only.

## What this file is not

- Not Option B (Autonomic Healing Core)
- Not a rewrite of `docs/autonomy_boundary.md`
- Not a `sed` update of `tests/test_root_bin_layers.py`

## YAML configuration examples

Copy-only templates. They do not replace sealed `ledger/*.yaml`.

Standalone files:

- `docs/examples/phase_lock.example.yaml`
- `docs/examples/dual_asgi.example.yaml`
- `docs/examples/ledger_append.example.yaml`

### Ledger fragment

```yaml
invariants:
  coherence: 1.0
  entropy: phi^{-1418}
  workload: 0.0
  phase_lock: 202.6
mcp:
  filled: false
  bind_0000: false
  dual_asgi: "127.0.0.1:8024"
```

### Dual ASGI env (never 0.0.0.0)

```yaml
env:
  - name: BIND
    value: "127.0.0.1"
  - name: DUAL_ASGI
    value: "127.0.0.1:8024"
  - name: FILLED
    value: "false"
```
