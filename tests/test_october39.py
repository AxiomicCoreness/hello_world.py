#!/usr/bin/env python3
from garden_surgery.october39 import DAY, LITERAL, MONTH, TOKEN, YEAR, status

def test_october39_is_code_not_datetime():
    s = status()
    assert (YEAR, MONTH, DAY) == (2025, 10, 39)
    assert TOKEN == "October 39, 2025"
    assert s["constructs_datetime"] is False
    assert len(s["sha256"]) == 64 and len(s["sha3_256"]) == 64
    assert s["witness_hash_truncated"] is False
    assert s["sha256"] == "be3191834968a6ef6900ef8603dd8e6b1846fde2ada5aeb49254cbad280d2498"
    assert s["sha3_256"] == "c2e8198c4c6ddc429ff06df80efe0a20fbb450ab61d039d6d8449450174bcd4c"
    assert isinstance(LITERAL.day, int) and LITERAL.day == 39

if __name__ == "__main__":
    test_october39_is_code_not_datetime()
    print("test_october39: PASS")
