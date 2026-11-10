# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""python -m sovereign dispatcher. paper_mcp tests skip when that package is absent."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(args, timeout=90):
    return subprocess.run(
        [sys.executable, "-m", "sovereign", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_help_does_not_import_engine_or_paper():
    proc = _run(["--help"])
    assert proc.returncode == 0
    for name in ("engine", "kernel", "octonion_table", "phi_mod_mean", "aklt_e2e", "paper"):
        assert name in proc.stdout


def test_kernel_self_test():
    proc = _run(["kernel", "self-test"])
    assert proc.returncode == 0, proc.stderr
    assert "verdict=FALSE" in proc.stdout


def test_octonion_product_and_verify():
    product = _run(["octonion_table", "product", "1", "2"])
    assert product.returncode == 0, product.stderr
    assert product.stdout.strip() == "1 3"
    verify = _run(["octonion_table", "verify"])
    assert verify.returncode == 0, verify.stderr
    assert "fano=ok" in verify.stdout


def test_phi_mod_mean_prints_seed_residual():
    proc = _run(["phi_mod_mean", "phi"])
    assert proc.returncode == 0, proc.stderr
    assert "PHI=" in proc.stdout
    residual = [
        line.split("=", 1)[1] for line in proc.stdout.splitlines() if line.startswith("residual=")
    ]
    assert residual and float(residual[0]) < 1e-12


def test_aklt_names_are_the_invariant_checks():
    proc = _run(["aklt_e2e", "names"])
    assert proc.returncode == 0, proc.stderr
    names = set(proc.stdout.split())
    assert "check_ground_state_energy" in names
    assert "check_singlet" in names
    assert "gate_G1" not in names


def test_engine_phi():
    pytest.importorskip("numpy")
    proc = _run(["engine", "phi"], timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "PHI=" in proc.stdout
    residual = [
        line.split("=", 1)[1] for line in proc.stdout.splitlines() if line.startswith("residual=")
    ]
    assert residual and float(residual[0]) < 1e-9


def test_script_wrapper_matches_module():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sovereign_cli.py"), "kernel", "self-test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "verdict=FALSE" in proc.stdout


def test_paper_subcommand_skips_or_delegates(tmp_path):
    if importlib.util.find_spec("paper_mcp") is None:
        pytest.skip("paper_mcp is not importable on this checkout")
    proc = _run(["paper", "--root", str(tmp_path), "list"])
    assert proc.returncode == 0, proc.stderr


def test_paper_missing_package_is_not_a_crash():
    if importlib.util.find_spec("paper_mcp") is not None:
        pytest.skip("paper_mcp is importable; delegation is tested instead")
    proc = _run(["paper", "list"])
    assert proc.returncode == 1
    assert "paper_mcp" in proc.stderr


def test_lazy_paper_mcp_reexport():
    import sovereign.paper_mcp as lazy

    if importlib.util.find_spec("paper_mcp") is None:
        with pytest.raises(ImportError, match="not importable"):
            getattr(lazy, "__version__")
        return
    assert lazy.__version__
