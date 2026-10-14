# ARCHITECTURE.md

What is on disk. What is not on disk is not claimed.

## 1. Package

`src/main/java/com/fruitfly/brain/`. Stdlib only. Compiles with `javac`. No Maven. No SLF4J.

| File | Role |
|---|---|
| `SovereignConstants.java` | phi, eta |
| `DarkStateInvariant.java` | lambda2 = 1 gate |
| `SovereigntyState.java` | 8-phase ladder |
| `LIFRK4.java` | neuron |
| `Connectome.java` | CSR + delay ring |
| `SovereignAutomaton.java` | swarm orchestrator |
| `GradientSynchronization.java` | Hebbian, eta = 1 |
| `AutonomousDriver.java` | self-starting entry |
| `SovereignMain.java` | CLI entry |

Compile:

```bash
javac -d out src/main/java/com/fruitfly/brain/*.java
```

## 2. Entry points

**AutonomousDriver** — self-starting. Depends on `SovereignConstants`, `DarkStateInvariant`, `SovereigntyState`, `LIFRK4`.

```bash
java -cp out com.fruitfly.brain.AutonomousDriver
```

Exit 0 on gate pass. Exit 1 on gate fail.

**SovereignMain** — CLI. Depends on `Connectome`, `SovereignAutomaton`, `GradientSynchronization`.

```bash
java -cp out com.fruitfly.brain.SovereignMain --chat "hello" --q 1.13 --p 25.96
java -cp out com.fruitfly.brain.SovereignMain --steps 3
```

`--q` and `--p` are passthrough. They are not computed by the class.

See `docs/RUNBOOK.md` for expected output and failure modes.

## 3. Seal convention

A computed seal is SHA3-256 of canonical JSON:

```json
{"body_sha3_256":"<hex>","entry_index":<int>,"event":"/<name>","file":"<path>"}
```

Serialization: `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.

A symbolic seal is a string of the form `\u2200\u221e\u03c6\u00b2 \u00b7 <NAME>_<N> \u00b7 <N>_SEALED`. It is a label, not a digest. The two are distinct fields. A symbolic seal is not recomputable from a preimage. A computed seal is.

HMAC is used in the JSONL stream (`ledger/witness_stream.jsonl`), not in the per-file seal. The HMAC key is `GARDEN` (public, documented). Algorithm: HMAC-SHA3-256. A public key proves adjacency: each line links to the prior. It does not prove authorship: anyone who can write the file can extend the chain with the same key.

The seal line itself is excluded from the preimage.

## 4. Current sealed surface

| Entry | File | Body SHA3-256 | Seal SHA3-256 | Commit |
|---|---|---|---|---|
| 540 | `aklt_invariants.py` | `fd035cd2...ba37` | `facc467e...5e68` | `924e94b8` |

Full values:

- body: `fd035cd230868996d591793843a0ec86b5d80333f4e402b67de1c17a440aba37`
- seal: `facc467ef838d0f47f2ccfe59193212ce119f53b79f899dd1437f2a748bb5e68`

## 5. Witness stream

`ledger/witness_stream.jsonl`. One JSON object per line. Each line carries `hmac_sha3_256` and `prev_hmac`. This stream begins at 540. Entries 1–539 are not in this stream. They are not bridged; they are absent.

| Entry | Event | HMAC | Prev |
|---|---|---|---|
| 540 | `/aklt_invariant_surface_sealed` | `a581983b...349a` | null |
| 541 | `/architecture_md_options_committed` | `761ccd9f...f99a` | 540's HMAC |
| 544 | `/structure_check_migrated` | `839e98bc...53bd` | 541's HMAC |

The stream ends at 544. Entries 542 and 543 are not in the stream.

## 6. Verification

1. Check out the commit named in the table.
2. Read the file. Strip header lines that begin with `# Seal:`, `# entry_index:`, `# seal_sha3_256:`, `# body_sha3_256:`, `# convention:`.
3. Compute SHA3-256 of the remaining bytes. Compare to the body hash.
4. Build the canonical JSON. Compute SHA3-256. Compare to the seal hash.

A mismatch is a disclosed defect, not a rewrite.

## 7. Ledger layout

`ledger/` holds per-index YAML entries and the JSONL stream. There is no single `ledger.yaml`. The chain links by the predecessor's declared seal. A content mismatch is recorded in a later entry; the earlier file is not rewritten.

## 8. What is not claimed

- No Merkle root for the full chain.
- No agent count, sheaf, PID gain, or reward pool.
- No authorship from the HMAC chain. The key is public. The chain proves adjacency only.
- Entries 1–539 are not in `witness_stream.jsonl`. The stream begins at 540.
- Entries 542 and 543 are not in the stream.
- This document is not itself a sealed chain entry.

## 9. Status

| Item | Value |
|---|---|
| Package | 9 files, stdlib, javac |
| Entries | AutonomousDriver, SovereignMain |
| Sealed | 540 |
| Stream | begins 540, ends 544 |
| Ledger rewrite | none |
