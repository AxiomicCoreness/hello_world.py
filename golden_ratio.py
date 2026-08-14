#!/usr/bin/env python3
"""Golden ratio foundation constants — Entry 8758 core."""
PHI = (1 + 5 ** 0.5) / 2
PHI_SQ = PHI + 1
PHI_INV = 1 / PHI
PHI_NEG2 = PHI ** -2  # == 1 - 2*PHI + PHI**2

if __name__ == "__main__":
    assert abs(PHI_SQ - (PHI * PHI)) < 1e-15
    assert abs((1 - 2 * PHI + PHI ** 2) - PHI_NEG2) < 1e-15
    print(f"PHI={PHI}")
    print(f"PHI_SQ={PHI_SQ}")
    print(f"PHI_NEG2={PHI_NEG2}")
