#!/usr/bin/env python3
"""systemd unit controller for the pulse script.

Writes a unit file. Does not install it. systemctl is not required.
__main__ clones the subject, runs the clone, and prints engine.C.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

PHI = (1.0 + 5.0 ** 0.5) / 2.0
SUBJECT = Path("pythonIDE/white_modification_to_pulse.py")


@dataclass
class Engine:
    C: float = 0.910

    def report(self) -> str:
        return f"engine.C={self.C:.6f}"


def unit_text(script: Path, user: str = "clarke") -> str:
    target = Path("/opt/hello_world.py") / script
    return (
        "[Unit]\n"
        "Description=White modification pulse script\n"
        "After=network-online.target\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"User={user}\n"
        f"WorkingDirectory=/opt/hello_world.py\n"
        f"ExecStart=/usr/bin/python3 {target}\n"
        "NoNewPrivileges=true\n"
        "PrivateTmp=true\n"
        "\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def write_unit(path: Path, script: Path) -> Path:
    path.write_text(unit_text(script), encoding="utf-8")
    return path


def clone_and_run(subject: Path) -> tuple[int, str]:
    if not subject.is_file():
        return 2, f"missing subject {subject}"
    digest = hashlib.sha3_256(subject.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="pulse-clone-") as tmp:
        clone = Path(tmp) / subject.name
        shutil.copyfile(subject, clone)
        if hashlib.sha3_256(clone.read_bytes()).hexdigest() != digest:
            return 1, "clone digest mismatch"
        proc = subprocess.run(
            [sys.executable, str(clone)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    tail = (proc.stdout or proc.stderr).strip().splitlines()
    last = tail[-1] if tail else ""
    return proc.returncode, last


def main() -> int:
    parser = argparse.ArgumentParser(prog="systemd_unit_controller")
    parser.add_argument("--subject", default=str(SUBJECT))
    parser.add_argument("--unit", default="white-modification-pulse.service")
    parser.add_argument("--write-unit", action="store_true")
    args = parser.parse_args()
    subject = Path(args.subject)
    engine = Engine()
    code, last = clone_and_run(subject)
    if args.write_unit and subject.is_file():
        written = write_unit(Path(args.unit), subject)
        print(f"unit={written}")
    print(engine.report())
    print(f"clone_exit={code}")
    print(f"clone_last={last}")
    return 0 if code == 0 else code


if __name__ == "__main__":
    sys.exit(main())
