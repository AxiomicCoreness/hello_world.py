# vendor/

DeepSeek inference kernels and DeepInfer live here as **git submodules**.

This first patch updates `.gitmodules` and ships pin documentation only.
Binary gitlinks are created by:

```bash
./scripts/init_deepinfer_vendors.sh
git add vendor/DeepInfer vendor/DeepGEMM vendor/FlashMLA vendor/DeepEP \
        vendor/DeepSelect vendor/DeepGEMM-Ascend vendor/DeepEP-Ascend
```

See `PINNED_SHAS.md` and `docs/deepinfer_integration.md`.
