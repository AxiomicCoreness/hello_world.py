# Make `scripts` importable from the skill root even under `python -P`
# (safe-path mode drops the working directory from sys.path).
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
