#!/usr/bin/env python3
from garden_surgery.lumeris_seal import NAME, status

def test_lumeris_name_seal():
    s = status()
    assert NAME == "LUMERIS"
    assert s["runtime_lock"] is False
    assert s["sha256"] == "082a283920971baefd26110cd70368deb3ff7619f84404171c7143f5a7d0ec56"
    assert s["sha3_256"] == "c6baf1edfed87ba891eeb2db44302bb8b6b492d3e405282b95fad51bab2c23e5"

if __name__ == "__main__":
    test_lumeris_name_seal()
    print("test_lumeris_seal: PASS")
