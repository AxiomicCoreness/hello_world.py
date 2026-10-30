# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Import-hygiene test for the top-level wood_dragon_technique.py.

Imports the module in a fresh ``python -I`` subprocess with a temporary HOME
and a temporary cwd, and checks that the import:
  * exits 0,
  * creates no files under HOME or cwd (no ~/Documents/Hyperian_Node, no
    phi_ngram_memory.json, no witness store),
  * opens no sockets (socket.socket is replaced before import),
  * leaves PredictorHandler state unloaded (lazy).

Third-party caches (matplotlib/fontconfig) are pointed at a separate scratch
dir so they cannot be confused with writes made by the module itself.

Works on Python 3.10 (uses -I, not -P).
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

pytest.importorskip("numpy")

REPO = pathlib.Path(__file__).resolve().parents[1]

CHILD = r'''
import json, socket, sys

class _NoSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        raise RuntimeError("socket opened during import")

socket.socket = _NoSocket
sys.path.insert(0, sys.argv[1])
import wood_dragon_technique as w

assert "[SIMULATION – static values]" in (w.__doc__ or ""), "simulation docstring missing"
assert w.PredictorHandler.memory is None, "PredictorHandler memory loaded at import"
print(json.dumps({
    "default": w.run_wood_dragon_technique(),
    "long": w.run_wood_dragon_technique(duration=100.0),
}, ensure_ascii=False))
'''


def _snapshot(root):
    found = set()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            found.add(os.path.relpath(os.path.join(dirpath, name), root))
    return found


def test_import_has_no_side_effects_and_technique_runs():
    with tempfile.TemporaryDirectory() as home, \
            tempfile.TemporaryDirectory() as cwd, \
            tempfile.TemporaryDirectory() as caches:
        before_home, before_cwd = _snapshot(home), _snapshot(cwd)
        env = {
            "HOME": home,
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "MPLCONFIGDIR": caches,
            "XDG_CACHE_HOME": caches,
            "XDG_CONFIG_HOME": caches,
            "MPLBACKEND": "Agg",
        }
        proc = subprocess.run(
            [sys.executable, "-I", "-B", "-c", CHILD, str(REPO)],
            cwd=cwd, env=env, capture_output=True, text=True, timeout=180,
        )
        assert proc.returncode == 0, proc.stderr[-4000:]
        assert _snapshot(home) == before_home, f"files created in HOME: {_snapshot(home) - before_home}"
        assert _snapshot(cwd) == before_cwd, f"files created in cwd: {_snapshot(cwd) - before_cwd}"

    out = json.loads(proc.stdout.strip().splitlines()[-1])
    default = out["default"]
    # Honest values for the defaults (chakra=1000, duration=10, rate=1/phi):
    # 1000 * (1 - exp(-10/phi)) = 997.930276 -> NOT fully drained.
    assert default["chakra_drained"] == pytest.approx(997.930276, abs=1e-6)
    assert default["fully_drained"] is False
    # A long enough duration does fully drain.
    assert out["long"]["fully_drained"] is True
