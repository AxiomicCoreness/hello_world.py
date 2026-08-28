"""Phase 6 sheaf: sections over the ledger. Not a loop.

Evolve = one-shot hash of the successor spec.
Logarithm-noose is lifted as a restriction word, not as a trainer.
"""
from __future__ import annotations
from typing import Dict
from garden_surgery.learner_hash import learner_sha3_256
from garden_surgery.self_write import successor_spec
from garden_surgery.cambrian_stub import allocation
PHASE = 6
LOOP = False

def section(next_index: int = 9104) -> Dict[str, object]:
    spec = successor_spec(next_index)
    digest = learner_sha3_256({"phase": PHASE, "spec": spec})
    stub = allocation()
    return {
        "phase": PHASE,
        "sheaf": "section",
        "loop": LOOP,
        "evolve": "one_shot_learner_hash",
        "learner_sha3_256": digest,
        "logarithm_noose": "lifted",
        "logarithm_is_not_a_gate": True,
        "alpha_eff_actual": 0.0,
        "optimizer": False,
        "cambrian_filled": stub["filled"],
        "rewire": "learner_hash <- self_write.successor_spec",
    }

if __name__ == "__main__":
    spec = section()
    print("phase:", spec["phase"])
    print("loop:", spec["loop"])
    print("evolve:", spec["evolve"])
    print("noose:", spec["logarithm_noose"])
    print("digest:", spec["learner_sha3_256"])
    print("cambrian_filled:", spec["cambrian_filled"])
