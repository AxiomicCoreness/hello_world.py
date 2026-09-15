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
    HBAR_DEN,
    HBAR_FRACTION,
    HBAR_NUM,
    HBAR_PER_UNIT,
    HOLDS,
    NOTES,
    VISION,
    WITNESS,
)


def test_stub_flag():
    # Stub guard — intentional.
    assert FILLED is False


def test_hbar_natural_units_string():
    # Stub guard — intentional.
    # The substring "natural-units" is the consumer contract.
    assert "natural-units" in NOTES["hbar_units"]
    assert "not SI" in NOTES["hbar_units"]


def test_hbar_integer_representation():
    # Exact rational — no float anywhere in this assertion path.
    assert NOTES["hbar_numerator"] == 1
    assert NOTES["hbar_denominator"] == 144
    assert NOTES["hbar_per_unit"] == 144
    assert NOTES["hbar_fraction"] == (1, 144)

    assert HBAR_NUM == 1
    assert HBAR_DEN == 144
    assert HBAR_PER_UNIT == 144
    assert HBAR_FRACTION == (1, 144)

    for k in ("hbar_numerator", "hbar_denominator", "hbar_per_unit"):
        assert isinstance(NOTES[k], int), f"{k} must be int, not {type(NOTES[k])}"

    assert isinstance(NOTES["hbar_fraction"], tuple)
    assert all(isinstance(x, int) for x in NOTES["hbar_fraction"])


def test_hbar_no_float_leakage():
    for k, v in NOTES.items():
        if k.startswith("hbar_") and k != "hbar_units":
            assert not isinstance(v, float), f"float leaked into {k}"


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
    assert f"{HBAR_NUM}/{HBAR_DEN}" in WITNESS
    assert "natural-units" in WITNESS
