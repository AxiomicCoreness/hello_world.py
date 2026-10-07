#!/usr/bin/env python3
from garden_surgery.fleck_split import DECAY_COEF, KAPPA_TR, identities, split

def test_fleck_identities():
    i = identities()
    assert i["eleven_cubed"] == 1331
    assert abs(KAPPA_TR - 88.99689437998485) < 1e-9
    assert abs(DECAY_COEF - 986.9906831399546) < 1e-9
    assert split()["entry_9040_untouched"] is True

if __name__ == "__main__":
    test_fleck_identities()
    print("test_fleck_split: PASS")
