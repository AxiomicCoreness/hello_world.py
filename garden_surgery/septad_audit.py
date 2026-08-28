"""Septad audit correction. Hashes are event SHA3-256, not git SHAs."""

from __future__ import annotations

from typing import Dict, List, Tuple

from garden_surgery.theorems import check_theorems, event_hash

SPINE: List[Tuple[int, str, str]] = [
    (9094, "/ci_cd/garden_surgery_workflow", "facfdd8232209d9f6e8c813f13cd55356b32f36a9c48f7b2b043f971d3d724b2"),
    (9095, "/ci_cd/argo_image_cd_combinator", "a03a9be816df14db73e54a12a59477de448c009be6ede205c6fdccefedf214b0"),
    (9096, "/frb/bridge_name_seal_no_public_bind", "dbf719cc61930be6d7d4e55d6c1d27f207ece9edc37e4725bb7610e527904cb3"),
    (9097, "/success_state/ket_refactored", "129524ec6513b841e90927d3e75234e428e721ec6c943ed3ea24c2cbf41d5d0e"),
]

LAYER_LEFT = "01e79bff1bef845d48142e73905c6874"
LAYER_RIGHT = "e2c07c1332672a425d776e644100507c"
GIT_HEAD_9097 = "d57501e2d4325a169a86e866a154f5cb40ceb0ea"


def report() -> Dict[str, object]:
    rows = []
    ok = True
    for index, event, expected in SPINE:
        got = event_hash(index, event)
        match = got == expected
        ok = ok and match
        rows.append({"index": index, "match": match, "hex": got})
    return {
        "theorems_ok": check_theorems().ok(),
        "spine_ok": ok,
        "rows": rows,
        "git_head_9097": GIT_HEAD_9097,
        "git_head_is_not_event_hash": True,
        "layer": {
            "left": LAYER_LEFT,
            "right": LAYER_RIGHT,
            "width_hex": 32,
            "kind": "128-bit token pair, not SHA3-256",
            "on_chain": False,
        },
        "rejected_claims": [
            "T2 as C(t) exponential",
            "T3 as theta=202.6 only",
            "cron 0 */6 live",
            "OIDC live",
            "DIRECT_IPC_PIPE bound",
            "event hash == git sha",
        ],
    }


if __name__ == "__main__":
    spec = report()
    print("theorems_ok:", spec["theorems_ok"])
    print("spine_ok:", spec["spine_ok"])
    for row in spec["rows"]:
        print(row["index"], "OK" if row["match"] else "FAIL", row["hex"])
    print("layer", spec["layer"]["left"] + "\u2022" + spec["layer"]["right"])
    print("on_chain:", spec["layer"]["on_chain"])
