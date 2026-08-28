"""|success> is theorems + matching event hashes. Not a QEC decoder."""

from __future__ import annotations

from typing import Dict, List, Tuple

from garden_surgery.theorems import check_theorems, event_hash

SEALED: List[Tuple[int, str, str]] = [
    (9094, "/ci_cd/garden_surgery_workflow", "facfdd8232209d9f6e8c813f13cd55356b32f36a9c48f7b2b043f971d3d724b2"),
    (9095, "/ci_cd/argo_image_cd_combinator", "a03a9be816df14db73e54a12a59477de448c009be6ede205c6fdccefedf214b0"),
    (9096, "/frb/bridge_name_seal_no_public_bind", "dbf719cc61930be6d7d4e55d6c1d27f207ece9edc37e4725bb7610e527904cb3"),
]


def audit() -> Dict[str, object]:
    report = check_theorems()
    rows = []
    hashes_ok = True
    for index, event, expected in SEALED:
        got = event_hash(index, event)
        match = got == expected
        hashes_ok = hashes_ok and match
        rows.append({"index": index, "match": match, "hex": got})
    success = bool(report.ok() and hashes_ok)
    return {
        "ket": "|success>" if success else "|open>",
        "theorems_ok": report.ok(),
        "hash_auditable": True,
        "hashes_match": hashes_ok,
        "qec_runtime": False,
        "qec_meaning": "invariants T1-T4, not a decoder",
        "rows": rows,
    }


if __name__ == "__main__":
    spec = audit()
    print("ket:", spec["ket"])
    print("theorems_ok:", spec["theorems_ok"])
    print("hashes_match:", spec["hashes_match"])
    print("qec_runtime:", spec["qec_runtime"])
    for row in spec["rows"]:
        print(row["index"], "OK" if row["match"] else "FAIL", row["hex"])
