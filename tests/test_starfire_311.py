from garden_surgery.autonomous_starfire_311 import (
    OMEGA_FIRE_DEG,
    OMEGA_FIRE_RAD,
    PHI,
    fire_payload,
    legend,
)


def test_omega_is_pi_over_phi():
    import math

    assert abs(OMEGA_FIRE_RAD - math.pi / PHI) < 1e-12
    assert abs(OMEGA_FIRE_DEG - 111.24611797498106) < 1e-9


def test_fire_is_symbolic():
    report = fire_payload()
    assert report["daemon"] is False
    assert report["status"] == "SYMBOLIC_ONLY"
    assert report["stillness"]["dragon_is_one"] is True


def test_legend_keys():
    body = legend()
    assert "omega_fire" in body["legend"]
    assert body["fusion_canonical"] == 515
    assert body["hyperion_preserved"] == 516
