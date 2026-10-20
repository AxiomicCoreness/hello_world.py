"""Run evals/bms_dom_test.js (node + jsdom) against assets/demo.html.

Set BMS_NODE_PATH to a node_modules folder that contains jsdom if it is not
globally resolvable. Skips when node or jsdom is missing (exit 77).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_dom_suite_in_jsdom():
    env = dict(os.environ)
    if os.environ.get("BMS_NODE_PATH"):
        env["NODE_PATH"] = os.environ["BMS_NODE_PATH"]
    r = subprocess.run(
        ["node", str(ROOT / "evals" / "bms_dom_test.js")],
        capture_output=True, text=True, env=env, timeout=120,
    )
    if r.returncode == 77:
        pytest.skip("jsdom not installed (npm install jsdom, then set BMS_NODE_PATH)")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.rstrip().endswith(" passed, 0 failed")
