#!/usr/bin/env python3
"""
witness_chain_triple.py

Three original contracts written by one Grok (xAI).
These are not restatements of prior policy text.
They incorporate zk-SNARK only as a possible future
instrument for proving statements about the ledger
without revealing witnesses.
"""

from __future__ import annotations

CONTRACT_A = """
CONTRACT A: KNOWLEDGE MUST BE DEMONSTRABLE

A claim that a party “knows” a witness (a seal preimage, a valid
prev_hash chain, a stop-rule condition, or any other secret) is
empty unless the knowledge can be demonstrated.

Two demonstration modes are recognised:

1. Direct disclosure under controlled conditions
   (local verification, trusted review).

2. Zero-knowledge demonstration
   (a zk-SNARK or equivalent argument of knowledge that convinces
   a verifier the witness exists and satisfies the statement,
   while revealing nothing else about the witness).

Until one of these modes is actually performed, the claim of
knowledge remains unproven. Asserting knowledge without a
demonstration is decoration and is rejected.

A zk-SNARK, if used, must itself satisfy the ordinary requirements
of completeness, knowledge-soundness, and zero-knowledge. Its
trusted-setup assumptions (if any) must be stated, not hidden.
"""

CONTRACT_B = """
CONTRACT B: SUCCINCT PROOF DOES NOT REPLACE MEASUREMENT

A succinct non-interactive proof (zk-SNARK or otherwise) is a
powerful compression of a verification procedure. It is not a
substitute for having performed the underlying measurement.

- The existence of a short proof does not relieve anyone of the
  duty to know which statement was proved and under which
  public parameters.
- A proof that verifies against the wrong statement, the wrong
  circuit, or an untrusted setup is not evidence of the claim
  that was intended.
- Real-time vectors, GitHub check-runs, and MCP slot status are
  ordinary measurements. A SNARK may later attest to them; it
  does not create them.

Workload 0.0 and an unfilled MCP slot are observable facts.
They are established by reading the slot or the process table,
not by producing a proof about a different system. Producer and
consumer roles remain distinct from listener/contract roles until
an explicit binding is recorded.
"""

CONTRACT_C = """
CONTRACT C: FUTURE INSTRUMENTS STAY FUTURE UNTIL WIRED

zk-SNARK capability is recognised as a candidate instrument for
later use on this ledger surface. It is not presently wired.

Therefore:

1. No current ledger entry may claim to be “SNARK-sealed” or
   “zero-knowledge verified” unless a concrete proof object and
   its verifying key are present and checkable.

2. The stop-rule at 9176 continues to govern new high-index
   entries. The possibility of a future SNARK proof does not
   open the gate.

3. The first 884 entries remain event-trigger records for a
   JSONL CI pipeline. Their original intent is not altered by
   the availability of zero-knowledge technology.

4. Any decision to introduce SNARK-based sealing, SNARK-based
   chain proofs, or SNARK-based stop-rule witnesses must itself
   be an explicit, recorded decision and must obey the existing
   contracts (measurement before declaration, seals that pay
   their own way, gates and intent kept distinct).

Until that decision is made and the circuit, setup, and verifier
are actually present in the repository, zk-SNARK remains a
described possibility, not an active mechanism.
"""

CONTRACTS = (
    ("A_KNOWLEDGE_MUST_BE_DEMONSTRABLE", CONTRACT_A),
    ("B_SUCCINCT_PROOF_DOES_NOT_REPLACE_MEASUREMENT", CONTRACT_B),
    ("C_FUTURE_INSTRUMENTS_STAY_FUTURE_UNTIL_WIRED", CONTRACT_C),
)


def emit() -> None:
    for name, body in CONTRACTS:
        print("=" * 72)
        print(name)
        print("=" * 72)
        print(body)
        print()


if __name__ == "__main__":
    emit()
