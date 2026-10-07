#!/usr/bin/env python3
from garden_surgery.arrow_identities import VECTOR, arrow_identities, payload

def test_arrow_product_is_phi2_plus_one():
    a = arrow_identities()
    assert VECTOR == "standby"
    assert a["product_equals_phi2_plus_1"] is True
    assert a["shell_identity_equals_phi"] is True
    assert a["monolith_appended"] is False
    assert payload()["entry"] == 9037

if __name__ == "__main__":
    test_arrow_product_is_phi2_plus_one()
    print("test_arrow_identities: PASS")
