# tests/test_vision_code_frequency_fleck_paste.py
#
# Stub guard: these assertions fail by design when the module is
# no longer a stub. When this test breaks, replace the stub guards
# with real assertions on the filled output — do NOT delete them.
#
# See: POLICY.md, ledger entry 9130.

from garden_surgery.vision_code_frequency_fleck_paste import (
    CODE_NOT_PORTED,
    FILLED,
    FREQUENCY,
    HOLDS,
    NOTES,
    VISION,
    WITNESS,
)


def test_stub_flag():
    # Stub guard — intentional.
    assert FILLED is False


def test_hbar_natural_units():
    # Stub guard — intentional. ħ := 1/144 is a natural-units convention, not SI.
    assert "natural-units" in NOTES["hbar_units"]
    assert "not SI" in NOTES["hbar_units"]


def test_holds_immutable():
    import pytest

    with pytest.raises(TypeError):
        HOLDS["φ⁸"] = 0.0  # type: ignore[index]


def test_frequency_immutable():
    import pytest

    with pytest.raises(TypeError):
        FREQUENCY["base"] = 0.0  # type: ignore[index]


def test_holds_values():
    assert HOLDS["φ⁸"] == 46.9787137637
    assert HOLDS["11³"] == 1331
    assert FREQUENCY["declared_as"] == "ω_P"
    assert FREQUENCY["base"] == 71.975


def test_vision_membership():
    assert "Q = 1700" in VISION


def test_witness_derived_not_drifted():
    for v in VISION:
        assert v in WITNESS
    for c in CODE_NOT_PORTED:
        assert c in WITNESS
