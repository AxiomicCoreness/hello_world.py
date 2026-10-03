#!/usr/bin/env python3
"""JAX mirror of scripts/traffic_cop.py. Not a second router.

The 55 names are imported from the sibling file. This module does not
copy the table. JAX is used only for the integer slot formula.
String lookup is outside jit. No socket. No dispatch.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import jax
import jax.numpy as jnp

_SRC = Path(__file__).with_name("traffic_cop.py")
_spec = importlib.util.spec_from_file_location("traffic_cop", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
FILES = _mod.FILES
N = len(FILES)


@jax.jit
def slot_index(day: jnp.int32, hour: jnp.int32, minute: jnp.int32) -> jnp.int32:
    total_minutes = day * jnp.int32(1440) + hour * jnp.int32(60) + minute
    return (total_minutes // jnp.int32(15)) % jnp.int32(N)


def slot_name(day: int, hour: int, minute: int) -> str:
    idx = int(slot_index(jnp.int32(day), jnp.int32(hour), jnp.int32(minute)))
    if not 0 <= idx < N:
        raise ValueError(f"slot out of 0-{N - 1}")
    return FILES[idx]


if __name__ == "__main__":
    print(slot_name(0, 0, 0))
    print(int(slot_index(jnp.int32(0), jnp.int32(0), jnp.int32(0))))
