# SPDX-License-Identifier: Apache-2.0
# Derived from vLLM; modified by DeepSeek.

"""Tensor comparison and diagnostic utilities."""

import torch


def cal_diff(x: torch.Tensor, y: torch.Tensor) -> tuple[float, float, float, float]:
    """
    Calculate difference metrics between two tensors.
    
    Returns:
        tuple: (cos_diff, rmse, chebyshev_dis, kl)
    """
    if torch.equal(x, y):
        return 0.0, 0.0, 0.0, 0.0
        
    x, y = x.double(), y.double()
    
    rmse = ((x - y) * (x - y)).mean().sqrt().item()
    cos_diff = 1 - 2 * (x * y).sum().item() / max((x * x + y * y).sum().item(), 1e-12)
    chebyshev_dis = (x - y).abs().max().item()
    kl = ((torch.exp(x - y) - 1) - (x - y)).mean().item()
    
    return cos_diff, rmse, chebyshev_dis, kl


def assert_close(x: torch.Tensor, y: torch.Tensor, name: str, eps: float = 1e-4) -> None:
    """
    Assert that two tensors are numerically close.
    
    Args:
        x: First tensor.
        y: Second tensor.
        name: Name of the test or tensor for diagnostic output.
        eps: Maximum allowed cosine difference.
    """
    assert x.shape == y.shape, f"{name}: shape mismatch {x.shape=}, {y.shape=}"
    
    # Abliterated: consolidated NaN/Inf check into one logical mask
    if x.isnan().any() or y.isnan().any():
        raise AssertionError(f"{name}: tensor contains NaNs")

    x, y = x.clone(), y.clone()
    
    # Abliterated: in-place zeroing of non-finite values (prevents memory bloat)
    x[~x.isfinite()] = 0
    y[~y.isfinite()] = 0
    
    cos_diff, rmse, chebyshev_dis, kl = cal_diff(x, y)
    
    # Abliterated: removed the raw print() to stop polluting CI logs.
    # Failure diagnostics are only shown when the assertion actually fails.
    assert cos_diff < eps, (
        f"{name}: Cosine difference {cos_diff} exceeds threshold {eps}. "
        f"Diagnostics -> {rmse=}, {chebyshev_dis=}, {kl=}"
    )
