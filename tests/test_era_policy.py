#!/usr/bin/env python3
from garden_surgery.era_policy import IGNORED_ERAS, status

def test_era_ignore():
    assert "anthropic_claude" in IGNORED_ERAS
    assert status()["pid_wigner_runtime"] is False

if __name__ == "__main__":
    test_era_ignore()
    print("test_era_policy: PASS")
