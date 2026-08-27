#!/usr/bin/env python3
from garden_surgery.october39 import ISO_DATE, TOKEN, status, token_digest

def test_token_is_legend_not_date():
    s = status()
    assert TOKEN == "October 39 2025"
    assert s["is_iso8601_date"] is False
    assert ISO_DATE is False
    assert s["october_has_31_days"] is True
    assert len(token_digest()) == 64

if __name__ == "__main__":
    test_token_is_legend_not_date()
    print("test_october39: PASS")
