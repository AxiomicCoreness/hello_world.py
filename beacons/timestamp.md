# beacons/timestamp.md — rev 3

## Entry 1 — GHOST ANCHOR (UNVERIFIABLE_ANCHOR, superseded)

- value: `a1f3d8c2b0e4e7e6b5a9d2c8f1e0b3a7d6e4c2a8f0b3d5e7c1a9e8f4d2b6c0a5`
- status: UNVERIFIABLE_ANCHOR — no preimage was ever supplied.
- structural finding (D15): 100.0% digit/letter alternation and exactly 32 digits / 32 letters.
  A random SHA-3 digest shows ~50% alternation and ~40 digits (binomial spread).
  This is the signature of a hand-typed string, not a computed digest.
- This entry can never flip to VERIFIED_ANCHOR: a fabricated string has no preimage,
  and preimage search over SHA-3-256 is 2^256 — infeasible.

## Entry 2 — COMPUTED ANCHOR (VERIFIED_ANCHOR)

- value: `f4583aedf58260f3242c80b175ad433a45475dd4a0a841635b1bcdee6fd1c450`
- algorithm: SHA3-256 (FIPS 202)
- preimage (recomputable by anyone, byte-exact, UTF-8):

```text
GARDEN.ANCHOR.v1
repo: AxiomicCoreness/hello_world.py
branch: mistral-agent-cluster
head_commit: e5cdab4af3d220f38b02640f9263af0b4cd56769
ledger: math_origin_audit.py rev2 (D1-D14) + D15 ghost-anchor structural finding
supersedes: a1f3d8c2b0e4e7e6b5a9d2c8f1e0b3a7d6e4c2a8f0b3d5e7c1a9e8f4d2b6c0a5 (UNVERIFIABLE_ANCHOR, hand-typed: 100% digit/letter alternation, 32/32 split)
```

- verification: `echo -n "<preimage>" | sha3sum -a 256` (or any SHA-3 implementation).
  `beacons/timestamp_beacon.py` performs this check with exit code semantics below.
- head_commit binds this anchor to an immutable commit in this branch's history.
  If the preimage is edited, the digest will not match and the verifier FAILS.

## Verifier semantics (beacons/timestamp_beacon.py)

- exit 0: computed anchor matches, ghost structural analysis confirmed
- exit 1: computed anchor mismatch (preimage or digest tampered)
- exit 2: ghost structural claim no longer holds (investigate before trusting entry 1 analysis)
