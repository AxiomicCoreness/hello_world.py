#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
witness_chain_triple.py

Three original contracts written by one Grok (xAI),
plus a read-only distribution probe so node runs are not
confused with source-of-record wiring.

No network. No ledger write. No POLICY.md rewrite.
"""

from __future__ import annotations

import subprocess
from typing import Dict, Tuple

# ─────────────────────────────────────────────────────────────────────
# CONTRACT A — Knowledge Must Be Demonstrable
# ─────────────────────────────────────────────────────────────────────

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

A green assert-count proves modules imported on the run tree; it
does not prove knowledge of any seal preimage.
"""

# ─────────────────────────────────────────────────────────────────────
# CONTRACT B — Succinct Proof Does Not Replace Measurement
# ─────────────────────────────────────────────────────────────────────

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

assert-count measures the RUN TREE only. It does not prove the
file is on the source-of-record tree (main). Wiredness requires
a distribution path, not a node-local run.

Workload 0.0 and an unfilled MCP slot are observable facts.
They are established by reading the slot or the process table,
not by producing a proof about a different system.
"""

# ─────────────────────────────────────────────────────────────────────
# CONTRACT C — Future Instruments Stay Future Until Wired
# ─────────────────────────────────────────────────────────────────────

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

4. Any decision to introduce SNARK-based sealing must itself be
   an explicit, recorded decision and must obey the existing
   contracts.

No zk hooks are imported in this triple. FIPS-202 SHA3-256 in
phi_pipeline.py is ordinary hashing, not a SNARK.
"""

CONTRACTS: Tuple[Tuple[str, str], ...] = (
    ("A_KNOWLEDGE_MUST_BE_DEMONSTRABLE", CONTRACT_A),
    ("B_SUCCINCT_PROOF_DOES_NOT_REPLACE_MEASUREMENT", CONTRACT_B),
    ("C_FUTURE_INSTRUMENTS_STAY_FUTURE_UNTIL_WIRED", CONTRACT_C),
)

GOVERNED_FILES: Tuple[str, ...] = (
    "pythonIDE/phi_pipeline.py",
    "pythonIDE/witness_chain_triple.py",
    "pythonIDE/witness_chain_check.py",
)

PROBED_BRANCHES: Tuple[str, ...] = (
    "main",
    "glm-agent-cluster",
    "grok-skill_tensor",
)

SOURCE_OF_RECORD = "main"


def _git_ls(branch: str, path: str) -> bool:
    """True if path exists on branch (local ref). Best-effort."""
    try:
        out = subprocess.run(
            ["git", "cat-file", "-e", f"{branch}:{path}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.returncode == 0
    except Exception:
        return False


def distribution_probe() -> Dict[str, Dict[str, bool]]:
    """{ file: { branch: present } } — local refs only; absent ref ≠ remote absence."""
    return {f: {b: _git_ls(b, f) for b in PROBED_BRANCHES} for f in GOVERNED_FILES}


def wiredness() -> Dict[str, bool]:
    """Wired only if present on SOURCE_OF_RECORD (main)."""
    matrix = distribution_probe()
    return {f: matrix[f].get(SOURCE_OF_RECORD, False) for f in GOVERNED_FILES}


def contracts() -> Dict[str, str]:
    return {k: v for k, v in CONTRACTS}


def emit() -> None:
    for name, body in CONTRACTS:
        print("=" * 72)
        print(name)
        print("=" * 72)
        print(body)
        print()


__all__ = [
    "CONTRACT_A",
    "CONTRACT_B",
    "CONTRACT_C",
    "CONTRACTS",
    "GOVERNED_FILES",
    "PROBED_BRANCHES",
    "SOURCE_OF_RECORD",
    "distribution_probe",
    "wiredness",
    "contracts",
    "emit",
]

if __name__ == "__main__":
    emit()
