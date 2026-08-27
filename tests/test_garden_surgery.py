#!/usr/bin/env python3
"""Hard-fail tests for garden_surgery. No secret values."""

from garden_surgery.theorems import check_theorems, event_hash, KNOWN_HASHES, PHI, PHI2
from garden_surgery.environment import probe_environment


def test_theorems_all_pass():
    r = check_theorems()
    assert r.ok(), r.failed
    assert abs(PHI2 - (PHI + 1)) < 1e-15


def test_known_event_hashes():
    for (idx, ev), expected in KNOWN_HASHES.items():
        assert event_hash(idx, ev) == expected


def test_env_never_leaks_values():
    r = probe_environment()
    blob = str(r.as_dict())
    # report may contain key NAMES but not typical secret-shaped values
    assert "sk-" not in blob
    assert r.offline_viable is True
    for v in r.present.values():
        assert isinstance(v, bool)


if __name__ == "__main__":
    test_theorems_all_pass()
    test_known_event_hashes()
    test_env_never_leaks_values()
    print("test_garden_surgery: PASS")
