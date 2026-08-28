from garden_surgery.lattice_48 import generate_48_point_lattice, summary, BASE_AZIMUTH


def test_48_rows_and_no_fire():
    rows = generate_48_point_lattice()
    s = summary(rows)
    assert len(rows) == 48
    assert s["fire"] == 0.0
    assert s["c"] == 1.0
    assert abs(s["sum_w"] - 0.5429913027995648) < 1e-12
    assert int(s["peak_L"]) == 4
    assert int(s["peak_A"]) in (0, 2)
    assert s["peak_w"] < 0.9
    assert abs(BASE_AZIMUTH * ((1 + 5**0.5) / 2) - 180.0) < 1e-12


def test_odd_azimuths_near_zero_weight():
    rows = generate_48_point_lattice()
    odd = [row["w"] for row in rows if int(row["A"]) % 2 == 1]
    assert max(odd) < 1e-30


if __name__ == "__main__":
    test_48_rows_and_no_fire()
    test_odd_azimuths_near_zero_weight()
    print("test_lattice_48: PASS")
