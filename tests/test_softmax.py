"""
tests/test_softmax.py
Locks pythonIDE/softmax.py at version 1.1.0.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

try:
    from pythonIDE.softmax import softmax
except ImportError:
    import importlib.util
    _p = Path(__file__).resolve().parents[1] / "pythonIDE" / "softmax.py"
    _spec = importlib.util.spec_from_file_location("softmax", _p)
    _m = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_m)
    softmax = _m.softmax


def _close(a, b, tol=1e-6):
    return np.allclose(np.asarray(a), np.asarray(b), atol=tol)


def test_scalar_known_values():
    out = softmax([1, 2, 3])
    assert _close(out, [0.090030573, 0.244728471, 0.665240956])


def test_scalar_sums_to_one():
    out = softmax([1, 2, 3])
    assert abs(float(np.sum(out)) - 1.0) < 1e-12


def test_singleton_is_one():
    out = softmax([42.0])
    assert _close(out, [1.0])


def test_uniform_input_is_uniform_output():
    out = softmax([7.0, 7.0, 7.0, 7.0])
    assert _close(out, [0.25, 0.25, 0.25, 0.25])


def test_shift_invariance():
    a = softmax([1, 2, 3])
    b = softmax([101, 102, 103])
    assert _close(a, b, tol=1e-9)


def test_numerical_stability_large_magnitude():
    out = softmax([1000.0, 1000.0, 1000.0])
    assert _close(out, [1 / 3, 1 / 3, 1 / 3])


def test_numerical_stability_no_overflow():
    out = softmax([1000.0, 999.0, 998.0])
    assert not np.any(np.isnan(out))
    assert not np.any(np.isinf(out))
    assert abs(float(np.sum(out)) - 1.0) < 1e-12


def test_2d_row_wise_sum():
    out = softmax([[1, 2], [3, 4]])
    assert _close(np.sum(out, axis=1), [1.0, 1.0])


def test_2d_row_wise_known_values():
    out = softmax([[1, 2], [3, 4]])
    expected = [
        [0.268941421, 0.731058579],
        [0.268941421, 0.731058579],
    ]
    assert _close(out, expected)


def test_2d_non_shift_equivalent_rows():
    out = softmax([[1, 2], [1, 10]])
    expected = [
        [0.268941421, 0.731058579],
        [0.000123394, 0.999876606],
    ]
    assert _close(out, expected)
    assert not _close(out[0], out[1])


def test_2d_row_wise_not_column_wise():
    x = [[1, 2], [1, 10]]
    out = softmax(x)
    col_sums = np.sum(out, axis=0)
    row_sums = np.sum(out, axis=1)
    assert _close(row_sums, [1.0, 1.0])
    assert not _close(col_sums, [1.0, 1.0])


def test_cli_json_row_wise():
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "pythonIDE" / "softmax.py"),
            "--input",
            "[[1,2],[1,10]]",
            "--json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    arr = np.asarray(payload, dtype=float)
    assert arr.shape == (2, 2)
    assert _close(np.sum(arr, axis=1), [1.0, 1.0])


def test_cli_scalar_input():
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "pythonIDE" / "softmax.py"),
            "--input",
            "1 2 3",
            "--json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    arr = np.asarray(payload, dtype=float).ravel()
    assert abs(arr.sum() - 1.0) < 1e-12


@pytest.mark.parametrize("shape", [(3,), (4, 4), (2, 5, 3)])
def test_output_in_unit_interval(shape):
    rng = np.random.default_rng(0)
    x = rng.normal(size=shape)
    out = softmax(x)
    assert np.all(out >= 0.0)
    assert np.all(out <= 1.0)


@pytest.mark.parametrize("shape", [(3,), (4, 4), (2, 5, 3)])
def test_sums_to_one_along_last_axis(shape):
    rng = np.random.default_rng(1)
    x = rng.normal(size=shape)
    out = softmax(x)
    sums = np.sum(out, axis=-1)
    assert np.allclose(sums, 1.0, atol=1e-10)
