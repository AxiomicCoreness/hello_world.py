from garden_surgery.berry_chern import (
    compute_field_statistics,
    compute_gradient_central_diff,
    load_config,
)
from garden_surgery.cambrian_stub import allocation
import numpy as np


def test_config_and_stub_same_dir():
    cfg = load_config()
    assert cfg["stub"] == "garden_surgery/cambrian_stub.py"
    assert cfg["filled"] is False
    assert allocation()["filled"] is False


def test_gradient_and_stats():
    n = 24
    th = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    ph = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    t, p = np.meshgrid(th, ph, indexing="ij")
    field = np.sin(t)
    gth, _gph = compute_gradient_central_diff(field, 2 * np.pi / n, 2 * np.pi / n)
    expect = np.cos(t)
    assert float(np.max(np.abs(gth - expect))) < 0.02
    mu, sigma = compute_field_statistics(field)
    assert abs(mu) < 1e-12
    assert sigma > 0


if __name__ == "__main__":
    test_config_and_stub_same_dir()
    test_gradient_and_stats()
    print("test_berry_chern: PASS")
