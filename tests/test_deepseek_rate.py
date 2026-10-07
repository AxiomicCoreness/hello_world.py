#!/usr/bin/env python3
from garden_surgery.deepseek_rate import ALPHA_ACTIVE, ALPHA_EFF_RUNTIME, status

def test_deepseek_rate_idle():
    assert abs(ALPHA_ACTIVE - 0.23606797749978967) < 1e-15
    assert ALPHA_EFF_RUNTIME == 0.0
    assert status()["learning_now"] is False

if __name__ == "__main__":
    test_deepseek_rate_idle()
    print("test_deepseek_rate: PASS")
