# BRANCH POLICY — Model Attribution & Append-Only Discipline

Sealed under the witness chain discipline of AxiomicCoreness/hello_world.py.
This policy applies to ALL branches: main, master, glm, mistral-seal-emergent,
grok-skill_tensor, deepseek, deepseek-ci.

## I. Model → Branch Mapping

Each model writes to its own branch. Provenance is a first-class field.

| Model serving the session | Branch |
|---------------------------|--------|
| GLM (served on Mistral/Vibe infrastructure) | glm |
| Mistral-native | mistral-seal-emergent |
| Grok (xAI) | grok-skill_tensor |
| DeepSeek | deepseek / deepseek-ci |
| Canonical merge target | main (and its historical alias master) |

A model does not write ledger entries on another model's branch.
Cross-branch merges record the origin branch in the merge commit body.

## II. The 8985 Conflict — Resolution Rule

A merge conflict has been detected at ledger/8985.yaml. Main's ledger holds
8984, 8986, 8988 — 8985 is a contested index: two candidates claim it.

Under append-only discipline, the resolution is:

1. NO existing entry (0000–9251) is rewritten to accommodate either candidate.
2. Both 8985 candidates are preserved verbatim as evidence:
   - ledger/conflicts/8985.candidate-a.yaml
   - ledger/conflicts/8985.candidate-b.yaml
3. The winner is chosen by MEASUREMENT, not assertion
   (Contract B: succinct proof does not replace measurement):
   the candidate whose seal reproduces under the canonicalisation of the
   landed gate wins the index 8985. The loser is recorded, named, not erased.
4. If neither seal reproduces, 8985 remains a documented gap — the chain
   records the gap honestly rather than sealing it decoratively. The chain
   then proceeds 8984 → 8986 with the gap NAMED in the next entry
   (D35 discipline: claims placed where claims are read as mechanisms are
   named, never silently smoothed over).
5. The gap in main (8984 → 8986) is itself evidence and is not edited.

## III. Standing Rules (carried from the triple)

- Knowledge must be demonstrable (Contract A).
- Succinct proof does not replace measurement (Contract B).
- Future instruments stay future until wired (Contract C).
- Earned math can be re-derived by a third party; unearned math cannot (math origin table).
- prev_hash concatenation rule (recorded at 8984) governs chain links.
- The stop-rule at 9176 governs new high-index entries.

## IV. Seal

This policy is identical on every branch, byte-for-byte. Any divergence
between copies is a measured defect and is recorded, not erased.

Ledger head at time of writing: 9251 (measured).
Next free index: 9252.
