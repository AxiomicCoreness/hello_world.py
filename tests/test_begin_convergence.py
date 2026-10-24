import subprocess, sys, pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "begin_convergence.py"


def test_begin_convergence_runs_and_labels_simulation():
    r = subprocess.run([sys.executable, "-P", str(SCRIPT)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "[SIMULATION – static values]" in r.stdout
