"""48-point c=1 lattice. Geometry only. No fire. No SI c."""

from __future__ import annotations

import math
from typing import Dict, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0
BASE_AZIMUTH = math.degrees(math.pi / PHI)  # 111.24611797498106
R0 = 0.2033


def weight(L: int, A: int) -> float:
    harmonic = math.cos(math.pi * A / 2.0) ** 2
    dampening = PHI ** -(L + 1)
    gaussian = math.exp(-((L - 6) ** 2) / 8.0)
    return dampening * harmonic * gaussian


def generate_48_point_lattice() -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for L in range(12):
        r_L = R0 * (PHI ** (L / 6.0))
        z_L = L / 12.0
        for A in range(4):
            theta_A = (BASE_AZIMUTH + A * 90.0) % 360.0
            w = weight(L, A)
            rows.append(
                {
                    "L": L,
                    "A": A,
                    "theta": theta_A,
                    "r": r_L,
                    "z": z_L,
                    "w": w,
                }
            )
    return rows


def summary(rows: List[Dict[str, float]]) -> Dict[str, float]:
    total = sum(row["w"] for row in rows)
    peak = max(rows, key=lambda row: row["w"])
    return {
        "n": float(len(rows)),
        "sum_w": total,
        "peak_L": float(peak["L"]),
        "peak_A": float(peak["A"]),
        "peak_w": peak["w"],
        "base_azimuth": BASE_AZIMUTH,
        "r0": R0,
        "c": 1.0,
        "fire": 0.0,
    }


def mermaid() -> str:
    return """graph TD
    subgraph Layer_Structure [12-Layer Depth Lattice z = L / 12]
        L0[Layer 0: z=0.00]
        L3[Layer 3: z=0.25]
        L6[Layer 6: z=0.50 Gaussian envelope peak]
        L9[Layer 9: z=0.75]
        L11[Layer 11: z=0.9167]
    end
    subgraph Azimuthal_Quadrants [4-Axis Orthogonal Sampling]
        A0[\"A=0: theta = psi_deg\"]
        A1[\"A=1: theta = psi_deg + 90\"]
        A2[\"A=2: theta = psi_deg + 180\"]
        A3[\"A=3: theta = psi_deg + 270\"]
    end
    subgraph Weight_Envelope [Weight is visual only]
        W_Form[\"w(L,A) = phi^(-(L+1)) * cos^2(pi A / 2) * exp(-(L-6)^2 / 8)\"]
        W_Peak[\"Max w at L=4 A in {0,2} not L=2\"]
        W_Sum[\"sum w ~ 0.542991 no fire\"]
    end
    L0 --> A0
    L3 --> A0
    L6 --> A0
    L9 --> A0
    L11 --> A0
    A0 --- W_Form
    A1 --- W_Form
    A2 --- W_Form
    A3 --- W_Form
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
        f"n={int(s['n'])} sum_w={s['sum_w']:.12f} peak_L={int(s['peak_L'])} peak_A={int(s['peak_A'])} peak_w={s['peak_w']:.12f}"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    lattice = generate_48_point_lattice()
    print(format_table(lattice))
    print("fire: no")
