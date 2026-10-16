#!/usr/bin/env python3
"""
Core rendering engine for the AxiomicCoreness pipeline.
Supports multi-format output (PNG, SVG, PDF, EPS) with Matplotlib.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Headless / portable
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


def apply_style(style: str, font_family: str) -> None:
    """Apply a Matplotlib style and font family globally."""
    try:
        plt.style.use(style)
    except OSError:
        plt.style.use("default")
    matplotlib.rcParams["font.family"] = font_family
    matplotlib.rcParams["axes.unicode_minus"] = False


def load_data(path: Path) -> pd.DataFrame:
    """Load CSV or NumPy data."""
    if path.suffix == ".csv":
        return pd.read_csv(path)
    elif path.suffix in (".npy", ".npz"):
        return pd.DataFrame(np.load(path))
    else:
        raise ValueError(f"Unsupported data format: {path.suffix}")


def render_job(job: dict[str, Any], defaults: dict[str, Any], base_dir: Path) -> None:
    """Render a single job defined in the YAML config."""
    # Merge defaults and job-specific overrides
    cfg = {**defaults, **job}

    apply_style(cfg.get("style", "default"), cfg.get("font_family", "DejaVu Sans"))

    input_path = base_dir / cfg["input"]
    output_path = base_dir / cfg["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_data(input_path)

    fig, ax = plt.subplots(figsize=cfg.get("figsize", (8, 6)))

    plot_type = cfg.get("plot_type", "line")

    if plot_type == "line":
        ax.plot(
            df[cfg["x_col"]], df[cfg["y_col"]],
            color=cfg.get("color", "#00FFAA"),
            linewidth=cfg.get("linewidth", 2.0),
            label=cfg.get("label"),
        )
    elif plot_type == "scatter":
        ax.scatter(
            df[cfg["x_col"]], df[cfg["y_col"]],
            color=cfg.get("color", "#FF5555"),
            s=cfg.get("markersize", 4) ** 2,
            marker=cfg.get("marker", "o"),
            label=cfg.get("label"),
        )
    elif plot_type == "imshow":
        ax.imshow(df.values, cmap=cfg.get("cmap", "viridis"), aspect="auto")
        plt.colorbar(ax.images[0], ax=ax)
    elif plot_type == "bar":
        ax.bar(df[cfg["x_col"]], df[cfg["y_col"]], color=cfg.get("color", "#00FFAA"))
    else:
        raise ValueError(f"Unknown plot_type: {plot_type}")

    if "title" in cfg:
        ax.set_title(cfg["title"])
    if "xlabel" in cfg:
        ax.set_xlabel(cfg["xlabel"])
    if "ylabel" in cfg:
        ax.set_ylabel(cfg["ylabel"])
    if cfg.get("grid", True):
        ax.grid(True, alpha=0.3)

    if cfg.get("tight_layout", True):
        plt.tight_layout()

    fig.savefig(
        output_path,
        dpi=cfg.get("dpi", 300),
        format=cfg.get("format", "png"),
        bbox_inches=cfg.get("bbox_inches", "tight"),
        pad_inches=cfg.get("pad_inches", 0.1),
    )
    plt.close(fig)
    print(f"[render] {job['name']} -> {output_path} ({cfg.get('dpi', 300)} DPI, {cfg.get('format', 'png')})")


 def render_from_config(config_path: Path) -> None:
     """Parse YAML and render all jobs."""
     with open(config_path, "r") as f:
         config = yaml.safe_load(f)
 
     defaults = config.get("defaults", {})
     jobs = config.get("jobs", [])
-    base_dir = config_path.parent.parent  # Assume config is in tools/render/
+    # Config lives at <repo>/tools/render/render_config.yaml
+    # .parent -> tools/render, .parent -> tools, .parent -> <repo>
+    base_dir = config_path.resolve().parent.parent.parent

def main() -> None:
    parser = argparse.ArgumentParser(description="AxiomicCoreness Render Engine")
    parser.add_argument("--config", type=Path, default=Path("tools/render/render_config.yaml"))
    args = parser.parse_args()

    render_from_config(args.config)


if __name__ == "__main__":
    main()
