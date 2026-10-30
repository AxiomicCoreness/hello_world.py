# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""`/llm status`: what DeepInfer V4 (primary, 127.0.0.1:8090) still lacks on this machine,
and whether the reassembled deepseek-r2 GGUF (secondary tutor, 127.0.0.1:8085) is in place.

Reports, without importing the vendored ``deepinfer`` package (its ``__init__`` sets
process env vars and needs Python >= 3.12):

* Python version against upstream ``requires-python >=3.12``.
* The vendored tree (``deepinfer/VENDOR_MANIFEST.json``): every v4_modules file and
  every in-package parent module it imports is present and its git blob sha matches
  the DeepInfer pin.
* External GPU-stack modules (``importlib.util.find_spec``, no import): torch,
  deep_gemm, deep_ep, flash_mla, tile_kernels, tilelang, deep_select, deep_cluster,
  plus the compiled ``deepinfer._C`` (filesystem probe for ``_C*.so``), and CUDA.
* The GGUF ``deepseek-r2-1.5b-Q4_K_M.gguf`` in ``MODEL_DIR`` (default
  ``sovereign-irc-bridge/serving/models``, same as launch-8085-deepseek-r2.sh),
  size and full sha256 against the release value.

DeepInfer V4 code loads DeepSeek-V4.1 Hugging Face safetensors checkpoints, not GGUF;
the GGUF is only ever served by llama-server as the secondary tutor.

CLI (no network, works with ``python -I``)::

    python -I sovereign-irc-bridge/src/deepinfer_status.py status [--json] [--no-verify]
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

PIN = "9bd9cf243fc53ef9afbf8f04d391d989117d6ab9"
REQUIRES_PYTHON = (3, 12)
# Superset of llm_backend.CAPABILITY_MODULES (minus deepinfer._C, probed on disk below).
GPU_DEPS: Tuple[str, ...] = (
    "torch", "deep_gemm", "deep_ep", "flash_mla", "tile_kernels", "tilelang", "deep_select", "deep_cluster",
)
COMPILED_EXT = "deepinfer._C"
GGUF_NAME = "deepseek-r2-1.5b-Q4_K_M.gguf"
# Fallbacks; serving/models/MODEL_PIN.json overrides them when present.
GGUF_SHA256 = "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1"
GGUF_SIZE = 1_117_320_640
MODEL_PIN_PATH = Path(__file__).resolve().parents[1] / "serving" / "models" / "MODEL_PIN.json"


def load_model_pin(path: Path = MODEL_PIN_PATH) -> Dict[str, Any]:
    try:
        import json as _json
        return _json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


_PIN = load_model_pin()
if _PIN.get("file", GGUF_NAME) == GGUF_NAME:
    GGUF_SHA256 = str(_PIN.get("gguf_sha256", GGUF_SHA256))
    GGUF_SIZE = int(_PIN.get("size", GGUF_SIZE))
RELEASE_URL = "https://github.com/AxiomicCoreness/hello_world.py/releases/tag/model-deepseek-r2-1.5b-q4km-v1"
GGUF_URL = ("https://github.com/AxiomicCoreness/hello_world.py/releases/download/"
            "model-deepseek-r2-1.5b-q4km-v1/" + GGUF_NAME)
PREFIX = "[System] deepinfer status: "

_BRIDGE_DIR = Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return Path(os.environ.get("DEEPINFER_REPO_ROOT") or _BRIDGE_DIR.parent)


def model_dir() -> Path:
    return Path(os.environ.get("MODEL_DIR") or (_BRIDGE_DIR / "serving" / "models"))


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ------------------------------------------------------------------ vendored tree

def vendor_report(root: Optional[Path] = None) -> Dict[str, Any]:
    root = root or repo_root()
    mpath = root / "deepinfer" / "VENDOR_MANIFEST.json"
    if not mpath.is_file():
        return {"manifest": None, "total": 0, "missing": [], "drifted": [], "error": f"no manifest at {mpath}"}
    m = json.loads(mpath.read_text(encoding="utf-8"))
    missing: List[str] = []
    drifted: List[str] = []
    for f in m["files"]:
        p = root / f["path"]
        if not p.is_file():
            missing.append(f["path"])
            continue
        data = p.read_bytes()
        if f["mode"] == "repo_header_plus_upstream":
            marker = f["marker"].encode() + b"\n"
            data = data.split(marker, 1)[1] if marker in data else b""
        elif f["mode"] == "repo_stub_kept":
            continue
        if git_blob_sha(data) != f["blob_sha"]:
            drifted.append(f["path"])
    return {"manifest": str(mpath), "commit": m["commit"], "total": len(m["files"]),
            "missing": missing, "drifted": drifted, "error": None}


# ------------------------------------------------------------------ GPU stack

def _spec(name: str, find_spec: Callable[[str], Any]) -> bool:
    try:
        return find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def compiled_ext_present(root: Optional[Path] = None) -> bool:
    pkg = (root or repo_root()) / "deepinfer"
    pats = ("_C*.so", "_C*.pyd")
    if (pkg / "_C").is_dir():
        return True
    if any(next(pkg.glob(p), None) for p in pats):
        return True
    so = pkg / "_so"
    return so.is_dir() and any(next(so.glob(f"*/{p}"), None) for p in pats)


def _torch_cuda() -> bool:
    try:
        import torch  # type: ignore[import-not-found]

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001 - a broken torch just means "no CUDA"
        return False


def deps_report(find_spec: Callable[[str], Any] = importlib.util.find_spec,
                cuda_check: Callable[[], bool] = _torch_cuda,
                root: Optional[Path] = None) -> Dict[str, bool]:
    deps = {name: _spec(name, find_spec) for name in GPU_DEPS}
    deps[COMPILED_EXT] = compiled_ext_present(root)
    deps["cuda"] = bool(deps["torch"] and cuda_check())
    return deps


# ------------------------------------------------------------------ GGUF

_SHA_CACHE: Dict[Tuple[str, int, int], str] = {}
_SHA_LOCK = threading.Lock()


def sha256_file(path: Path) -> str:
    st = path.stat()
    key = (str(path), st.st_size, st.st_mtime_ns)
    with _SHA_LOCK:
        if key in _SHA_CACHE:
            return _SHA_CACHE[key]
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    with _SHA_LOCK:
        _SHA_CACHE[key] = digest
    return digest


def gguf_report(verify: bool = True, directory: Optional[Path] = None,
                expected_sha256: str = GGUF_SHA256, expected_size: Optional[int] = GGUF_SIZE) -> Dict[str, Any]:
    path = (directory or model_dir()) / GGUF_NAME
    out: Dict[str, Any] = {"path": str(path), "present": path.is_file(), "size": None,
                           "sha256": None, "verified": False, "state": "missing"}
    if not out["present"]:
        return out
    out["size"] = path.stat().st_size
    if expected_size is not None and out["size"] != expected_size:
        out["state"] = "size mismatch"
        return out
    if not verify:
        out["state"] = "present (sha256 not checked)"
        return out
    out["sha256"] = sha256_file(path)
    out["verified"] = out["sha256"] == expected_sha256
    out["state"] = "verified" if out["verified"] else "sha256 mismatch"
    return out


# ------------------------------------------------------------------ report

def report(verify: bool = True) -> Dict[str, Any]:
    py = sys.version_info[:3]
    vend = vendor_report()
    deps = deps_report()
    gguf = gguf_report(verify=verify)
    missing_deps = [d for d in (*GPU_DEPS, COMPILED_EXT) if not deps[d]]
    blockers = list(missing_deps)
    if py[:2] < REQUIRES_PYTHON:
        blockers.insert(0, f"python>={REQUIRES_PYTHON[0]}.{REQUIRES_PYTHON[1]}")
    if vend["missing"] or vend["drifted"] or vend["error"]:
        blockers.append("vendored tree incomplete/drifted")
    if not deps["cuda"]:
        blockers.append("CUDA GPU")
    return {"python": ".".join(map(str, py)), "python_ok": py[:2] >= REQUIRES_PYTHON,
            "vendor": vend, "deps": deps, "missing_deps": missing_deps, "gguf": gguf,
            "deepinfer_runnable_here": not blockers, "blockers": blockers}


def status_lines(verify: bool = True, rep: Optional[Dict[str, Any]] = None) -> List[str]:
    r = rep or report(verify=verify)
    v, g, d = r["vendor"], r["gguf"], r["deps"]
    lines = [PREFIX + f"python {r['python']} (upstream DeepInfer needs >=3.12: {'ok' if r['python_ok'] else 'TOO OLD'})"]
    if v["error"]:
        lines.append(PREFIX + f"vendored tree: {v['error']}")
    else:
        ok = v["total"] - len(v["missing"]) - len(v["drifted"])
        lines.append(PREFIX + f"vendored v4_modules + in-package parents: {ok}/{v['total']} files match "
                     f"DeepInfer@{v['commit']} (missing {len(v['missing'])}, drifted {len(v['drifted'])})"
                     + (f": {', '.join((v['missing'] + v['drifted'])[:5])}" if v["missing"] or v["drifted"] else ""))
    present = [m for m in (*GPU_DEPS, COMPILED_EXT) if d[m]]
    lines.append(PREFIX + "missing external deps: " + (", ".join(r["missing_deps"]) or "none")
                 + "; present: " + (", ".join(present) or "none") + f"; CUDA {'available' if d['cuda'] else 'unavailable'}")
    if g["state"] == "verified":
        gl = f"GGUF {GGUF_NAME} verified at {g['path']} (sha256 {g['sha256']})"
    elif g["state"] == "missing":
        gl = (f"GGUF {GGUF_NAME} missing at {g['path']} - download {GGUF_URL} (sha256 {GGUF_SHA256}) "
              f"or run sovereign-irc-bridge/serving/models/fetch-deepseek-r2.sh, which tries it "
              f"first and falls back to the 42 parts ({RELEASE_URL})")
    elif g["state"] == "sha256 mismatch":
        gl = f"GGUF at {g['path']} sha256 MISMATCH: {g['sha256']} != {GGUF_SHA256}"
    else:
        gl = f"GGUF at {g['path']}: {g['state']} (size {g['size']})"
    lines.append(PREFIX + gl)
    if r["deepinfer_runnable_here"]:
        lines.append(PREFIX + "verdict: DeepInfer V4 prerequisites present; serve it on 127.0.0.1:8090 "
                     "(see docs/DEEPINFER_8090_RUNBOOK.md)")
    else:
        lines.append(PREFIX + "verdict: DeepInfer V4 cannot run here (needs " + ", ".join(r["blockers"])
                     + "); it loads DeepSeek-V4.1 HF safetensors, not GGUF, so the GGUF stays the "
                     "secondary tutor on 127.0.0.1:8085 (docs/DEEPINFER_8090_RUNBOOK.md)")
    return lines


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="deepinfer_status", description=__doc__.splitlines()[0])
    ap.add_argument("command", nargs="?", default="status", choices=["status"])
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    ap.add_argument("--no-verify", action="store_true", help="skip the GGUF sha256 (size check only)")
    a = ap.parse_args(argv)
    rep = report(verify=not a.no_verify)
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        print("\n".join(status_lines(rep=rep)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
