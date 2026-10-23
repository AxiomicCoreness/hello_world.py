#!/usr/bin/env python3
"""One-shot helper: stage vendor gitlinks + README and push to main."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

README = textwrap.dedent(
    """\
    # vendor/

    DeepSeek inference kernels and DeepInfer live here as **git submodules**.

    Pins: see `PINNED_SHAS.md`. Materialize / refresh checkouts:

    ```bash
    ./scripts/init_deepinfer_vendors.sh
    ```

    Gitlinks on this branch (mode 160000) record DeepInfer + DeepGEMM + FlashMLA +
    DeepEP + DeepSelect (+ Ascend twins). DualPipe is deferred (training-only).

    `scripts/build_vendor.sh` runs `pip install -e vendor/DeepGEMM` when the
    checkout exists. CUDA kernel compile needs CUDA toolkit + GPU (Hopper/SM90+
    per upstream); without `CUDA_HOME` the full build fails — use a CUDA host or
    Kaniko/`argocd/Dockerfile.deepinfer` path.

    See `docs/deepinfer_integration.md`.
    """
)

MSG = textwrap.dedent(
    """\
    chore(vendor): materialize DeepGEMM + inference submodule gitlinks

    Checkout pins via init_deepinfer_vendors.sh so build_vendor.sh can
    pip install -e vendor/DeepGEMM. DeepGEMM @ 1fc9c669…; siblings match
    PINNED_SHAS.md. DualPipe deferred. CUDA kernel compile soft-limited
    without CUDA_HOME.

    Signed-off-by: Clarke Yoursa Tee <ClarkeYTee@users.noreply.github.com>
    """
)

VENDORS = [
    "vendor/DeepInfer",
    "vendor/DeepGEMM",
    "vendor/FlashMLA",
    "vendor/DeepEP",
    "vendor/DeepSelect",
    "vendor/DeepGEMM-Ascend",
    "vendor/DeepEP-Ascend",
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def main() -> None:
    Path("vendor/README.md").write_text(README)
    run(["git", "config", "user.name", "Clarke Yoursa Tee"])
    run(["git", "config", "user.email", "ClarkeYTee@users.noreply.github.com"])
    run(["git", "add", *VENDORS, "vendor/README.md"])
    out = subprocess.check_output(["git", "ls-files", "-s", "vendor/DeepGEMM"], text=True)
    print(out, flush=True)
    mode, sha, *_ = out.split()
    assert mode == "160000", mode
    assert sha == "1fc9c66975ee322d628b3288534ca0e9ce12a64d", sha
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("Nothing to commit — already materialized", flush=True)
        return
    run(["git", "commit", "-m", MSG])
    run(["git", "push", "origin", "HEAD:main"])


if __name__ == "__main__":
    main()
