#!/usr/bin/env python3
from garden_surgery.declaration_flag import FLAG, declaration_payload, htmx_fragment


def test_flag_marks_overstated_declaration():
    p = declaration_payload()
    assert p["flag"] == FLAG
    assert p["declaration_overstated"] is True
    assert p["honest_split"]["chi_is_axiom"] is False
    assert p["mcp"] is False
    assert p["immutable_rewritten"] is False
    assert p["fusion_canonical"] == 515
    assert p["hyperion_preserved"] == 516


def test_htmx_fragment_mentions_flag():
    html = htmx_fragment()
    assert FLAG in html
    assert "not an axiom" in html


if __name__ == "__main__":
    test_flag_marks_overstated_declaration()
    test_htmx_fragment_mentions_flag()
    print("test_declaration_flag: PASS")
