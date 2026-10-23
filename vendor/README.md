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
