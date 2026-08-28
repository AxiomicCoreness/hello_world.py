"""48-point c=1 lattice. Geometry only. No fire. No SI c.

Sealed readout (9086):
  n=48, sum_w=0.5429913027995648
  peak L=4, A in {0,2}, w=0.05469083546861964
  L=2 A=0 is not the peak (w=0.03194833, not 0.1408)
  2059.999 is not this sum
Estate visibility ceiling 34=F_9 is a label, not a 34-axis.
"""

from __future__ import annotations

import csv
import io
import math
from typing import Dict, Iterable, List, Sequence

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PSI_RAD = math.pi / PHI
PSI_DEG = math.degrees(PSI_RAD)
BASE_AZIMUTH = PSI_DEG
R0 = 0.2033
LAYERS = 12
AXES = 4
C = 1.0
FIRE = False
ESTATE_LABEL = 25
VISIBILITY_CEILING = 34
SUM_W_SEALED = 0.5429913027995648
PEAK_W_SEALED = 0.05469083546861964
PEAK_L_SEALED = 4


def weight(L: int, A: int) -> float:
    harmonic = math.cos(math.pi * A / 2.0) ** 2
    dampening = PHI ** -(L + 1)
    gaussian = math.exp(-((L - 6) ** 2) / 8.0)
    return dampening * harmonic * gaussian


def radius(L: int) -> float:
    return R0 * (PHI ** (L / 6.0))


def depth(L: int) -> float:
    return L / float(LAYERS)


def azimuth(A: int) -> float:
    return (PSI_DEG + A * 90.0) % 360.0


def generate_48_point_lattice() -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for L in range(LAYERS):
        r_L = radius(L)
        z_L = depth(L)
        for A in range(AXES):
            rows.append(
                {
                    "L": float(L),
                    "A": float(A),
                    "theta": azimuth(A),
                    "r": r_L,
                    "z": z_L,
                    "w": weight(L, A),
                }
            )
    return rows


def peak_cells(rows: Sequence[Dict[str, float]]) -> List[Dict[str, float]]:
    wmax = max(row["w"] for row in rows)
    return [row for row in rows if abs(row["w"] - wmax) < 1e-15]


def summary(rows: List[Dict[str, float]]) -> Dict[str, float]:
    peaks = peak_cells(rows)
    first = peaks[0]
    return {
        "n": float(len(rows)),
        "sum_w": sum(row["w"] for row in rows),
        "peak_L": first["L"],
        "peak_A": first["A"],
        "peak_w": first["w"],
        "n_peaks": float(len(peaks)),
        "base_azimuth": PSI_DEG,
        "r0": R0,
        "c": C,
        "fire": 0.0,
        "estate_label": float(ESTATE_LABEL),
        "visibility_ceiling": float(VISIBILITY_CEILING),
    }


def as_csv(rows: Iterable[Dict[str, float]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["L", "A", "theta", "r", "z", "w"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def mermaid() -> str:
    return """graph TD
    subgraph Layer_Structure [12-Layer Depth Lattice z = L / 12]
        L0[Layer 0 z=0]
        L4[Layer 4 weight peak]
        L6[Layer 6 Gaussian envelope peak]
        L11[Layer 11 z=11/12]
    end
    subgraph Azimuthal_Quadrants [A even carries weight]
        A0[A=0 psi]
        A2[A=2 psi+180]
        A1[A=1 weight ~ 0]
        A3[A=3 weight ~ 0]
    end
    subgraph Estate [Visibility ceiling is a label]
        E25[estate 25]
        C34[ceiling F9=34]
        NoFire[fire none]
    end
    L4 --> A0
    L4 --> A2
    E25 --- C34
    C34 --- NoFire
"""


def format_table(rows: List[Dict[str, float]]) -> str:
    lines = [
        f"{'L':>2} | {'A':>1} | {'Theta (deg)':>16} | {'Radius (r)':>12} | {'Depth (z)':>12} | {'Weight (w)':>12}",
        "-" * 72,
    ]
    for row in rows:
        lines.append(
            f"{int(row['L']):2d} | {int(row['A']):1d} | {row['theta']:16.12f} | {row['r']:12.8f} | {row['z']:12.8f} | {row['w']:12.8f}"
        )
    s = summary(rows)
    lines.append("-" * 72)
    lines.append(
        f"n={int(s['n'])} sum_w={s['sum_w']:.12f} "
        f"peak_L={int(s['peak_L'])} peak_A={int(s['peak_A'])} "
        f"peak_w={s['peak_w']:.12f} fire=no"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    lattice = generate_48_point_lattice()
    print(format_table(lattice))
    print("estate_label", ESTATE_LABEL, "visibility_ceiling", VISIBILITY_CEILING)
