"""Fukui-Hatsugai-Suzuki Berry curvature and Chern numbers.

Config and bin sit beside cambrian_stub.py. No daemon.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np

CONFIG_PATH = Path(__file__).with_name("berry_config.yaml")


def load_config(path: Path = CONFIG_PATH) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8")
    cfg: Dict[str, object] = {}
    headers: list = []
    stack = [cfg]
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.lstrip().partition(":")
        key = key.strip()
        val = val.strip()
        while headers and indent <= headers[-1][0]:
            headers.pop()
            stack.pop()
        section = stack[-1]
        if val == "":
            child: Dict[str, object] = {}
            section[key] = child
            headers.append((indent, key))
            stack.append(child)
        else:
            section[key] = _parse_scalar(val)
    return cfg


def _parse_scalar(val: str):
    if val in ("true", "false"):
        return val == "true"
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p.strip()) for p in inner.split(",")]
    try:
        if "." in val or "e" in val.lower():
            return float(val)
        return int(val)
    except ValueError:
        return val


def compute_berry_curvature_and_chern(eigenstates: np.ndarray):
    n_theta, n_phi, _dim, num_bands = eigenstates.shape
    f_ij = np.zeros((n_theta, n_phi, num_bands))
    for n in range(num_bands):
        u = eigenstates[:, :, :, n]
        u_d1 = np.roll(u, -1, axis=0)
        u_d2 = np.roll(u, -1, axis=1)
        inner_1 = np.einsum("ijk,ijk->ij", u.conj(), u_d1)
        inner_2 = np.einsum("ijk,ijk->ij", u.conj(), u_d2)
        denom_1 = np.maximum(np.abs(inner_1), 1e-15)
        denom_2 = np.maximum(np.abs(inner_2), 1e-15)
        u1 = inner_1 / denom_1
        u2 = inner_2 / denom_2
        u1_d2 = np.roll(u1, -1, axis=1)
        u2_d1 = np.roll(u2, -1, axis=0)
        plaquette = u1 * u2_d1 * u1_d2.conj() * u2.conj()
        f_ij[:, :, n] = np.angle(plaquette)
    chern = np.sum(f_ij, axis=(0, 1)) / (2.0 * np.pi)
    return f_ij, np.rint(chern).astype(int)


def compute_gradient_central_diff(phi_field, d_theta, d_phi):
    grad_theta = (np.roll(phi_field, -1, axis=0) - np.roll(phi_field, 1, axis=0)) / (2.0 * d_theta)
    grad_phi = (np.roll(phi_field, -1, axis=1) - np.roll(phi_field, 1, axis=1)) / (2.0 * d_phi)
    return grad_theta, grad_phi


def compute_field_statistics(field):
    return float(np.mean(field)), float(np.std(field))


def histogram_bins(field, cfg):
    bins_cfg = cfg.get("bins", {})
    n_bins = int(bins_cfg.get("field_hist", 32))
    rng = bins_cfg.get("range", [-np.pi, np.pi])
    return np.histogram(field, bins=n_bins, range=(float(rng[0]), float(rng[1])))


def demo_from_config(cfg):
    grid = cfg.get("grid", {})
    n_theta = int(grid.get("n_theta", 24))
    n_phi = int(grid.get("n_phi", 24))
    theta = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    th, ph = np.meshgrid(theta, phi, indexing="ij")
    field = np.sin(th) + np.cos(ph)
    dth = float(grid.get("theta_period", 2.0 * np.pi)) / n_theta
    dph = float(grid.get("phi_period", 2.0 * np.pi)) / n_phi
    gth, gph = compute_gradient_central_diff(field, dth, dph)
    mu, sigma = compute_field_statistics(field)
    counts, edges = histogram_bins(field, cfg)
    return {
        "n_theta": n_theta,
        "n_phi": n_phi,
        "mu_M": mu,
        "sigma": sigma,
        "grad_theta_rms": float(np.sqrt(np.mean(gth * gth))),
        "grad_phi_rms": float(np.sqrt(np.mean(gph * gph))),
        "hist_counts": counts.tolist(),
        "hist_edges": edges.tolist(),
        "cambrian_filled": False,
    }
