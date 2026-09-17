#!/usr/bin/env python3
"""Scalar matrix of affected Garden markdown → seaborn heatmap. Not Pythonista."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

PHI = (1 + 5**0.5) / 2
AFFECTED = [
    "POLICY.md",
    "README.md",
    "docs/SEARCH.md",
    "docs/phase_lock_definition.md",
    "docs/pydantic_v2_validators.md",
    "docs/pydantic_v2_model_validator.md",
    "docs/pydantic_v3_field_validator.md",
    "docs/fastMCP_spec.md",
    "docs/fastmcp_layer.md",
    "LEDGER_GAPS_README.md",
]
METRICS = ["bytes", "lines", "phi_scaled", "mentions_8024"]


def scan(root: Path):
    rows = []
    for rel in AFFECTED:
        p = root / rel
        if not p.is_file():
            rows.append([0, 0, 0.0, 0])
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        b = p.stat().st_size
        n = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
        m = text.count("127.0.0.1:8024") + text.count("8024")
        rows.append([b, n, (b / PHI), float(m)])
    return np.array(rows, dtype=float)


def plot(mat, out: Path) -> None:
    labels = [Path(p).name for p in AFFECTED]
    logm = np.log1p(mat)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        logm,
        ax=ax,
        xticklabels=METRICS,
        yticklabels=labels,
        cmap="mako",
        annot=np.round(mat, 1),
        fmt=".1f",
        cbar_kws={"label": "log1p under raw annot"},
    )
    ax.set_title("Affected *.md scalar matrix (pythonIDE / seaborn)")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)


def main() -> int:
    here = Path(__file__).resolve()
    root = here.parents[1]
    mat = scan(root)
    out = here.parent / "md_scalar_matrix.png"
    plot(mat, out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
