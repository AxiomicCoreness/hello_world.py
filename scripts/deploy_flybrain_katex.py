#!/usr/bin/env python3
"""
Deploys a 20-neuron flybrain mesh, wired to the KaTeX macro registry.
Neuron state is driven by macro domain loads (garden, math, physics).
Outputs a K8s ConfigMap holding the initialized connectome state.

Macros are loaded from docs/katex_macros.yaml (strict domain tree) — never
invented names. Canonical λ₀ Rule A = 952072.1 nm (θ_lock 202.6°).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
MACROS_PATH = ROOT / "docs" / "katex_macros.yaml"
OUT_PATH = ROOT / "flybrain-katex-state.yaml"

# Canonical Rule A (θ_lock = 202.6°): λ₀ = 2π·535805 / 3.536037 ≈ 952072.1 nm
CANONICAL_LAMBDA0_NM = 952072.1
THETA_LOCK_DEG = 202.6


def load_macros(path: Path) -> dict[str, list[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    domains = data["katex"]["macros"]
    out: dict[str, list[str]] = {}
    for domain in ("garden", "math", "physics"):
        if domain not in domains:
            raise SystemExit(f"missing KaTeX domain: {domain}")
        # Preserve YAML key order; keys are macro names like "\\half"
        out[domain] = list(domains[domain].keys())
    return out


def macro_to_current(macro_name: str) -> float:
    h = sum(ord(c) for c in macro_name)
    return (h % 100) / 10.0  # 0 to 10 nA


def main() -> int:
    macros = load_macros(MACROS_PATH)
    flat = macros["garden"] + macros["math"] + macros["physics"]
    n_macros = len(flat)
    if n_macros != 37:
        print(
            f"WARN: expected 37 macros in docs/katex_macros.yaml, found {n_macros}",
            file=sys.stderr,
        )

    n_neurons = 20
    np.random.seed(42)

    v_rest = -70.0
    v_thresh = -50.0
    v_reset = -65.0
    tau_m = 20.0  # ms
    dt = 1.0  # ms
    r_m = 10.0  # MOhm

    w = np.random.randn(n_neurons, n_neurons) * 0.5
    np.fill_diagonal(w, 0.0)

    neuron_macros = flat[:n_neurons]
    background_macros = flat[n_neurons:]
    i_ext = np.array([macro_to_current(m) for m in neuron_macros])

    v = np.ones(n_neurons) * v_rest
    spikes: list[dict] = []

    for step in range(100):
        i_bg = sum(macro_to_current(m) for m in background_macros) * 0.01
        i_total = i_ext + i_bg + w @ (v > v_rest).astype(float)
        dv = (-(v - v_rest) + r_m * i_total) / tau_m * dt
        v = v + dv
        spiked = v >= v_thresh
        if np.any(spiked):
            spikes.append({"step": step, "neurons": np.where(spiked)[0].tolist()})
            v[spiked] = v_reset

    state = {
        "neurons": n_neurons,
        "lambda0_nm": CANONICAL_LAMBDA0_NM,
        "theta_lock_deg": THETA_LOCK_DEG,
        "katex_source": str(MACROS_PATH.relative_to(ROOT)),
        "macros_by_domain": {k: len(v) for k, v in macros.items()},
        "macros_total": n_macros,
        "macros_wired": neuron_macros,
        "background_macros": background_macros,
        "spike_history": spikes,
        "final_voltage": v.tolist(),
        "connectome_shape": list(w.shape),
    }

    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "flybrain-katex-state",
            "namespace": "sovereign",
            "annotations": {
                "axiomiccoreness.io/lambda0-nm": str(CANONICAL_LAMBDA0_NM),
                "axiomiccoreness.io/katex-macros": str(n_macros),
            },
        },
        "data": {
            "state.json": json.dumps(state, indent=2),
        },
    }

    with OUT_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(configmap, f, sort_keys=False, default_flow_style=False)

    n_spike_events = sum(len(s["neurons"]) for s in spikes)
    print(f"Flybrain initialized: {n_neurons} neurons.")
    print(
        f"KaTeX wired from {MACROS_PATH.name}: "
        f"{len(neuron_macros)} active, {len(background_macros)} background "
        f"(total {n_macros}; garden={len(macros['garden'])} "
        f"math={len(macros['math'])} physics={len(macros['physics'])})."
    )
    print(f"Spikes recorded: {n_spike_events}")
    print(f"ConfigMap written: {OUT_PATH.name}")
    print(f"λ₀ Rule A canonical: {CANONICAL_LAMBDA0_NM} nm @ θ_lock={THETA_LOCK_DEG}°")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
