"""Offline tests for serving/models/fetch-deepseek-r2.sh.

No network: a fake ``curl`` on PATH serves assets from a local folder, and the
script's expected GGUF sha256 is substituted for the sha256 of tiny fake data.
"""
import hashlib
import io
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "serving" / "models" / "fetch-deepseek-r2.sh"
REAL_SHA = "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1"
GGUF = "deepseek-r2-1.5b-Q4_K_M.gguf"
ARCHIVE = "deepseek-r2-1.5b-Q4_K_M.tar.gz"
DATA = b"GGUF fake tutor weights for offline test\n" * 50

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")

FAKE_CURL = r"""#!/usr/bin/env bash
out=""; url=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o) out="$2"; shift 2;;
    --retry|--retry-delay) shift 2;;
    -*) shift;;
    *) url="$1"; shift;;
  esac
done
echo "${url##*/}" >> "$ASSETS/.requests"
src="$ASSETS/${url##*/}"
[ -f "$src" ] || exit 22
cp "$src" "$out"
"""


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _setup(tmp_path: Path, single: bytes = None, parts: bool = True):
    assets = tmp_path / "assets"; assets.mkdir()
    bindir = tmp_path / "bin"; bindir.mkdir()
    curl = bindir / "curl"; curl.write_text(FAKE_CURL); curl.chmod(0o755)
    script = tmp_path / "fetch.sh"
    script.write_text(SCRIPT.read_text().replace(REAL_SHA, _sha(DATA)))
    script.chmod(0o755)
    if single is not None:
        (assets / GGUF).write_bytes(single)
    if parts:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            ti = tarfile.TarInfo(GGUF); ti.size = len(DATA)
            tf.addfile(ti, io.BytesIO(DATA))
        arc = buf.getvalue()
        sums = [f"{_sha(arc)}  {ARCHIVE}", f"{_sha(DATA)}  {GGUF}"]
        chunk = max(1, len(arc) // 3 + 1)
        for i in range(0, len(arc), chunk):
            name = f"{ARCHIVE}.part-{i // chunk:03d}"
            (assets / name).write_bytes(arc[i:i + chunk]); sums.append(f"{_sha(arc[i:i + chunk])}  {name}")
        (assets / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    dest = tmp_path / "dest"
    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
               ASSETS=str(assets), DEST=str(dest))
    return script, env, dest, assets


def _run(script, env):
    return subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=60)


def _requests(assets: Path):
    p = assets / ".requests"
    return p.read_text().split() if p.exists() else []


def test_script_defaults_to_real_sha_and_release() -> None:
    s = SCRIPT.read_text()
    assert REAL_SHA in s and 'fetch "$GGUF"' in s and "model-deepseek-r2-1.5b-q4km-v1" in s
    assert "0.0.0.0" not in s


def test_single_file_used_when_verified(tmp_path: Path) -> None:
    script, env, dest, assets = _setup(tmp_path, single=DATA)
    r = _run(script, env)
    assert r.returncode == 0, r.stderr
    assert (dest / GGUF).read_bytes() == DATA
    assert "single-file asset" in r.stdout
    assert _requests(assets) == [GGUF]  # no parts downloaded


def test_falls_back_to_parts_when_single_missing(tmp_path: Path) -> None:
    script, env, dest, assets = _setup(tmp_path, single=None)
    r = _run(script, env)
    assert r.returncode == 0, r.stderr
    assert (dest / GGUF).read_bytes() == DATA
    assert "falling back to parts" in r.stderr
    assert "SHA256SUMS" in _requests(assets)


def test_falls_back_to_parts_when_single_mismatched(tmp_path: Path) -> None:
    script, env, dest, assets = _setup(tmp_path, single=DATA[:-7])  # truncated upload
    r = _run(script, env)
    assert r.returncode == 0, r.stderr
    assert (dest / GGUF).read_bytes() == DATA
    assert "sha256" in r.stderr and "falling back to parts" in r.stderr


def test_fails_when_single_mismatched_and_no_parts(tmp_path: Path) -> None:
    script, env, dest, _ = _setup(tmp_path, single=b"corrupt", parts=False)
    r = _run(script, env)
    assert r.returncode != 0
    assert not (dest / GGUF).exists()


def test_skip_single_forces_parts(tmp_path: Path) -> None:
    script, env, dest, assets = _setup(tmp_path, single=DATA)
    env["SKIP_SINGLE"] = "1"
    r = _run(script, env)
    assert r.returncode == 0, r.stderr
    assert GGUF not in _requests(assets)
