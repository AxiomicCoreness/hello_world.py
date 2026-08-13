#!/usr/bin/env python3
"""Entrypoint: python run_port380.py  (never runs install_k8s.sh as Python)."""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
runpy.run_path(str(Path(__file__).resolve().parent / "quantum" / "port_380_http.py"), run_name="__main__")
