#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
7D Hypersurface Projection — A14 Bionic / PythonIDE
===================================================
Renders a 7-dimensional hypersurface projected to 3D, with a 2D fallback
when mpl_toolkits.mplot3d is unavailable. ASCII fallback when matplotlib
is missing. Pure-math fallback when numpy is missing.

Target: iPhone 12 (A14 Bionic) running PythonIDE (not Pythonista).
Output: hypersurface_7d.png at 300 DPI, tight_layout applied when available.

Exit codes:
    0  render succeeded
    1  math_origin verification failed (φ identities broken)
    2  render failed (no output produced)
"""

import math
import sys

# ─────────────────────────────────────────────────────────────────
# OPTIONAL DEPENDENCIES — fallbacks decided at import time
# ─────────────────────────────────────────────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import matplotlib
    matplotlib.use("Agg")  # headless-safe on PythonIDE
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

HAS_3D = False
if HAS_MPL:
    try:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        HAS_3D = True
    except ImportError:
        HAS_3D = False


# ─────────────────────────────────────────────────────────────────
# φ-HARMONIC CONSTANTS
# ─────────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI2 = PHI ** 2
PHI_INV = 1 / PHI
PHI_INV2 = PHI_INV ** 2
PHI_INV3 = PHI_INV ** 3
PHI_INV4 = PHI_INV ** 4

# Display-only constants (see MATH_ORIGIN for status)
NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6

# Legacy constants — unused in current script body
F0 = 6.49
T_PHI = 0.5983

# 7D hypersurface sampling density
N = 40  # grid side; 40^7 would be enormous, so we sample along a 7-torus path


# ─────────────────────────────────────────────────────────────────
# MATH_ORIGIN REGISTRY
# Rule: no symbolic term without a mathematical origin + proven equivalence.
# Status values:
#   VERIFIED              — derivation + numerical identity confirmed
#   PENDING_MATH_ORIGIN   — value used but no derivation supplied
#   UNUSED                — defined but never referenced
#   DISPLAY_ONLY          — used only for labels, no mathematical claim
# ─────────────────────────────────────────────────────────────────
MATH_ORIGIN = {
    "PHI": {
        "value": PHI,
        "operator": "root of x^2 - x - 1 = 0",
        "derivation": "quadratic formula on x^2 - x - 1 = 0, positive root",
        "identity": "PHI^2 = PHI + 1",
        "verification": "abs(PHI**2 - PHI - 1) < 1e-15",
        "status": "VERIFIED",
        "symbolic_equivalence": "self-similar division (golden ratio)",
    },
    "PHI2": {
        "value": PHI2,
        "operator": "PHI + 1",
        "derivation": "PHI^2 - PHI - 1 = 0  =>  PHI^2 = PHI + 1",
        "verification": "abs(PHI2 - (PHI + 1)) < 1e-15",
        "status": "VERIFIED",
    },
    "PHI_INV": {
        "value": PHI_INV,
        "operator": "PHI - 1",
        "derivation": "PHI^2 = PHI + 1  =>  PHI = 1 + 1/PHI  =>  1/PHI = PHI - 1",
        "verification": "abs(PHI_INV - (PHI - 1)) < 1e-15",
        "status": "VERIFIED",
    },
    "PHI_INV2": {
        "value": PHI_INV2,
        "operator": "2 - PHI",
        "derivation": "(PHI - 1)^2 = PHI^2 - 2*PHI + 1 = (PHI+1) - 2*PHI + 1 = 2 - PHI",
        "verification": "abs(PHI_INV2 - (2 - PHI)) < 1e-15",
        "status": "VERIFIED",
    },
    "PHI_INV3": {
        "value": PHI_INV3,
        "operator": "PHI_INV * PHI_INV2",
        "derivation": "product of previous two",
        "verification": "abs(PHI_INV3 - (PHI_INV * PHI_INV2)) < 1e-15",
        "status": "VERIFIED",
    },
    "PHI_INV4": {
        "value": PHI_INV4,
        "operator": "PHI_INV2 ** 2",
        "derivation": "square of PHI_INV2",
        "verification": "abs(PHI_INV4 - (PHI_INV2 ** 2)) < 1e-15",
        "status": "VERIFIED",
    },
    "NORTH_STAR_HZ": {
        "value": NORTH_STAR_HZ,
        "derivation": None,
        "status": "PENDING_MATH_ORIGIN",
        "note": "Used in figure title only. Supply a derivation, "
                "or reclassify as DISPLAY_ONLY and rename to remove the "
                "NORTH_STAR claim.",
    },
    "PHASE_LOCK_DEG": {
        "value": PHASE_LOCK_DEG,
        "derivation": None,
        "status": "PENDING_MATH_ORIGIN",
        "note": "Used in figure title only. Same disposition as NORTH_STAR_HZ.",
    },
    "F0": {
        "value": F0,
        "derivation": None,
        "status": "UNUSED",
        "note": "Defined but not referenced. Either wire in or remove.",
    },
    "T_PHI": {
        "value": T_PHI,
        "derivation": None,
        "status": "UNUSED",
        "note": "Defined but not referenced. Same disposition as F0.",
    },
}


def verify_math_origins(eps=1e-15):
    """
    Verify every VERIFIED math_origin holds numerically.
    Returns (failures, pending): failures is a list of strings (each is a
    broken identity); pending is a list of keys still awaiting derivation.
    """
    failures = []

    if abs(PHI ** 2 - PHI - 1.0) > eps:
        failures.append("PHI: x^2 - x - 1 != 0")
    if abs(PHI2 - (PHI + 1.0)) > eps:
        failures.append("PHI2: PHI^2 != PHI + 1")
    if abs(PHI_INV - (PHI - 1.0)) > eps:
        failures.append("PHI_INV: 1/PHI != PHI - 1")
    if abs(PHI_INV2 - (2.0 - PHI)) > eps:
        failures.append("PHI_INV2: PHI_INV^2 != 2 - PHI")
    if abs(PHI_INV3 - (PHI_INV * PHI_INV2)) > eps:
        failures.append("PHI_INV3: product mismatch")
    if abs(PHI_INV4 - (PHI_INV2 ** 2)) > eps:
        failures.append("PHI_INV4: square mismatch")

    pending = [
        k for k, v in MATH_ORIGIN.items()
        if v.get("status") in ("PENDING_MATH_ORIGIN", "UNUSED")
    ]
    return failures, pending


# ─────────────────────────────────────────────────────────────────
# 7D HYPERSPACE — sample along a φ-harmonic 7-torus, project to 3D
# ─────────────────────────────────────────────────────────────────
def hypersurface_7d(n_samples):
    """
    Return 7 coordinate arrays sampled along a φ-harmonic torus in R^7.
    Each coordinate is driven by a φ-scaled frequency so the projected
    surface is non-degenerate.
    """
    ts = [2 * math.pi * i / (n_samples - 1) for i in range(n_samples)]

    w = [1.0, PHI, PHI2, PHI_INV, PHI_INV2, PHI_INV3, PHI_INV4]

    phases = [PHASE_LOCK_DEG * math.pi / 180 * (k + 1) / 7 for k in range(7)]
    thetas = [[w[k] * t + phases[k] for t in ts] for k in range(7)]

    coords = [[math.cos(thetas[k][i]) for i in range(n_samples)] for k in range(7)]

    envelope = [
        1.0 - 0.1 * math.exp(-((i - n_samples / 2) ** 2) / (2 * (n_samples / 8) ** 2))
        for i in range(n_samples)
    ]
    for k in range(7):
        coords[k] = [coords[k][i] * envelope[i] for i in range(n_samples)]

    return coords


def project_7d_to_3d(coords):
    """
    Orthogonal-ish projection of R^7 → R^3 using φ-weighted directions.
    """
    n = len(coords[0])

    dirs = [
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (PHI_INV, PHI_INV, 0.0),
        (0.0, PHI_INV, PHI_INV),
        (PHI_INV, 0.0, PHI_INV),
        (PHI_INV2, PHI_INV2, PHI_INV2),
    ]

    x = [0.0] * n
    y = [0.0] * n
    z = [0.0] * n
    for k in range(7):
        d = dirs[k]
        ck = coords[k]
        for i in range(n):
            x[i] += d[0] * ck[i]
            y[i] += d[1] * ck[i]
            z[i] += d[2] * ck[i]

    for arr in (x, y, z):
        lo = min(arr)
        hi = max(arr)
        rng = (hi - lo) if (hi - lo) > 1e-12 else 1.0
        for i in range(len(arr)):
            arr[i] = 2.0 * (arr[i] - lo) / rng - 1.0

    return x, y, z


# ─────────────────────────────────────────────────────────────────
# RENDERERS
# ─────────────────────────────────────────────────────────────────
def render_3d(x, y, z, outfile):
    """3D scatter + line renderer with tight_layout at 300 DPI."""
    fig = plt.figure(figsize=(8, 8), dpi=300, facecolor="#0a0e1a")
    ax = fig.add_subplot(111, projection="3d", facecolor="#0a0e1a")

    ax.plot(x, y, z, color="#7fffd4", linewidth=0.6, alpha=0.9, label="7D torus path")
    ax.scatter(x, y, z, c=z, cmap="plasma", s=4, alpha=0.85)

    ax.set_xlabel("X", color="#8fa3bf", fontsize=8)
    ax.set_ylabel("Y", color="#8fa3bf", fontsize=8)
    ax.set_zlabel("Z", color="#8fa3bf", fontsize=8)
    ax.set_title(
        "7D φ-Harmonic Hypersurface → 3D Projection\n"
        f"North Star {NORTH_STAR_HZ} Hz · Phase {PHASE_LOCK_DEG}° · A14 Bionic",
        color="#e8e8e8", fontsize=10,
    )
    ax.tick_params(colors="#555577", labelsize=7)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.grid(True, alpha=0.15, color="#555577")
    ax.view_init(elev=25, azim=45)

    try:
        plt.tight_layout()
    except Exception as e:
        print(f"⚠️  tight_layout skipped: {type(e).__name__}: {e}")

    fig.savefig(outfile, dpi=300, bbox_inches="tight", facecolor="#0a0e1a")
    plt.close(fig)
    return outfile


def render_2d(x, y, z, outfile):
    """2D fallback — three orthogonal projections side by side."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=300, facecolor="#0a0e1a")

    pairs = [("X", x, "Y", y), ("X", x, "Z", z), ("Y", y, "Z", z)]
    for ax, (lx, xa, ly, ya) in zip(axes, pairs):
        ax.set_facecolor("#0a0e1a")
        ax.scatter(xa, ya, c=z, cmap="plasma", s=3, alpha=0.8)
        ax.plot(xa, ya, color="#7fffd4", linewidth=0.3, alpha=0.5)
        ax.set_xlabel(lx, color="#8fa3bf", fontsize=8)
        ax.set_ylabel(ly, color="#8fa3bf", fontsize=8)
        ax.tick_params(colors="#555577", labelsize=6)
        for spine in ax.spines.values():
            spine.set_color("#333344")
        ax.grid(True, alpha=0.15, color="#555577")

    fig.suptitle(
        "7D Hypersurface — 2D Projections (mpl_toolkits.mplot3d unavailable)",
        color="#e8e8e8", fontsize=10,
    )

    try:
        plt.tight_layout()
    except Exception as e:
        print(f"⚠️  tight_layout skipped: {type(e).__name__}: {e}")

    fig.savefig(outfile, dpi=300, bbox_inches="tight", facecolor="#0a0e1a")
    plt.close(fig)
    return outfile


def render_ascii(coords):
    """Last-resort fallback: no matplotlib."""
    x, y, _ = project_7d_to_3d(coords)
    W, H = 60, 24
    grid = [[" "] * W for _ in range(H)]
    for xi, yi in zip(x, y):
        col = int((xi + 1) / 2 * (W - 1))
        row = int((1 - (yi + 1) / 2) * (H - 1))
        col = max(0, min(W - 1, col))
        row = max(0, min(H - 1, row))
        grid[row][col] = "·"
    print("┌" + "─" * W + "┐")
    for row in grid:
        print("│" + "".join(row) + "│")
    print("└" + "─" * W + "┘")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    outfile = "hypersurface_7d.png"

    print(f"numpy:      {'yes' if HAS_NUMPY else 'no — pure-math fallback'}")
    print(f"matplotlib: {'yes' if HAS_MPL else 'no — ASCII fallback'}")
    print(f"mplot3d:    {'yes' if HAS_3D else 'no — 2D fallback'}")
    print(f"target:     A14 Bionic / PythonIDE")
    print()

    # ── math_origin gate ─────────────────────────────────────────
    failures, pending = verify_math_origins()
    if failures:
        print("❌ math_origin verification failed:")
        for f in failures:
            print(f"     {f}")
        return 1
    print(f"✅ math_origin: {len(MATH_ORIGIN) - len(pending)} verified")
    if pending:
        print(f"⚠️  pending/unused: {', '.join(pending)}")
    print()

    coords = hypersurface_7d(N)
    if HAS_NUMPY:
        coords = [np.asarray(c, dtype=np.float64) for c in coords]
    x, y, z = project_7d_to_3d(coords)

    if HAS_MPL and HAS_3D:
        path = render_3d(x, y, z, outfile)
        print(f"✅ 3D render → {path} (300 DPI, tight_layout)")
        return 0
    elif HAS_MPL:
        path = render_2d(x, y, z, outfile)
        print(f"✅ 2D render → {path} (300 DPI, tight_layout)")
        return 0
    else:
        print("⚠️  matplotlib missing — ASCII projection only:")
        render_ascii(coords)
        return 2


if __name__ == "__main__":
    sys.exit(main())
