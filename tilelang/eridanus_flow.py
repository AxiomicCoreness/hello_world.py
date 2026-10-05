#!/usr/bin/env python3
"""Surface 3. Named only. N and A are not constructed."""

from __future__ import annotations

import importlib.util
import py_compile
import sys
from pathlib import Path

FAMILY = "eridanus_flow"
SIBLING_FAMILY = "evolanus_flow"
SPLIT_SURFACES = {"eridanus_flow": 3, "evolanus_flow": 4}


def phi_action(n_defined: bool, a_defined: bool, x):
    if not (n_defined and a_defined):
        raise RuntimeError("N or A undefined; Phi not constructed")
    return x


def hermitian_guard(c_is_hermitian: bool) -> None:
    # C Hermitian implies iC anti-Hermitian, so Phi has an imaginary spectrum.
    if not c_is_hermitian:
        raise SystemExit(2)


def cross_ref_check() -> None:
    if SPLIT_SURFACES != {"eridanus_flow": 3, "evolanus_flow": 4}:
        raise SystemExit(1)
    sibling = Path(__file__).with_name("evolanus_flow.py")
    text = sibling.read_text(encoding="utf-8")
    if 'SPLIT_SURFACES = {"eridanus_flow": 3, "evolanus_flow": 4}' not in text:
        raise SystemExit(1)
    if 'FAMILY = "evolanus_flow"' not in text:
        raise SystemExit(1)
    py_compile.compile(str(sibling), doraise=True)
    spec = importlib.util.spec_from_file_location("evolanus_flow_sibling", sibling)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.FAMILY != SIBLING_FAMILY or mod.SPLIT_SURFACES != SPLIT_SURFACES:
        raise SystemExit(1)


def main() -> int:
    cross_ref_check()
    hermitian_guard(True)
    try:
        phi_action(False, False, None)
    except RuntimeError:
        print("SURFACE 3 named-only refusal held")
    print(FAMILY, SPLIT_SURFACES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
