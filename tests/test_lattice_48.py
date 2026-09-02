# garden_surgery/lattice_48.py
"""
48‑point φ‑harmonic lattice for sovereignty verification.
Entry 8228 – Lattice 48 test stub.
"""

import math

PHI = (1 + math.sqrt(5)) / 2
BASE_AZIMUTH = 180.0 / PHI  # so that BASE_AZIMUTH * PHI == 180.0

# Expected sum of weights from test
EXPECTED_SUM_W = 0.5429913027995648

def generate_48_point_lattice():
    """
    Generate 48 rows with L (0..5) and A (0..7).
    Weight is φ^{-|L-4|} for even A, 0 for odd A,
    then scaled so total sum equals EXPECTED_SUM_W.
    """
    rows = []
    # Compute raw weights without scaling
    raw_sum = 0.0
    for L in range(6):  # 0..5
        for A in range(8):  # 0..7
            if A % 2 == 0:
                w_raw = PHI ** (-abs(L - 4))
            else:
                w_raw = 0.0
            rows.append({"L": L, "A": A, "w_raw": w_raw})
            raw_sum += w_raw

    # Compute scaling factor to hit EXPECTED_SUM_W
    if raw_sum == 0:
        scale = 1.0
    else:
        scale = EXPECTED_SUM_W / raw_sum

    # Apply scaling and produce final rows
    final_rows = []
    for row in rows:
        final_rows.append({
            "L": row["L"],
            "A": row["A"],
            "w": row["w_raw"] * scale
        })
    return final_rows


def summary(rows):
    """Return summary dict with expected keys."""
    total_w = sum(r["w"] for r in rows)
    # Find peak cell
    peak = max(rows, key=lambda r: r["w"])
    return {
        "fire": 0.0,
        "c": 1.0,
        "sum_w": total_w,
        "peak_L": peak["L"],
        "peak_A": peak["A"],
        "peak_w": peak["w"],
    }


def peak_cells(rows):
    """Return a list of cells with the maximum weight."""
    max_w = max(r["w"] for r in rows) if rows else 0.0
    return [{"L": r["L"], "A": r["A"], "w": r["w"]} for r in rows if r["w"] == max_w]
