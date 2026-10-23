# Make `rmd_scripts` importable from the skill root even under `python -P`
# (safe-path mode drops the working directory from sys.path). The package is
# `rmd_scripts`, not `scripts`, so it cannot shadow the repo's top-level `scripts/`.
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
