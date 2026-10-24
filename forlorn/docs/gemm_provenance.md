# GEMM Provenance & Execution Paths

This document clarifies the matrix multiplication (GEMM) backends used across the AxiomicCoreness stack, distinguishing between what is theoretically available and what actually executes on the current hardware.

## 1. Hardware Context
* **Target Host**: CPU-only machine (supports Intel AMX).
* **GPU Availability**: None (No Hopper GPUs present).

## 2. GEMM Backend Matrix

| Layer / Component | Backend Used | Hardware | Notes |
| :--- | :--- | :--- | :--- |
| **`vendor/DeepGEMM`** | DeepGEMM (FP8) | Hopper GPU | Specialized FP8 kernels. **Not active** on current CPU host. Kept in `vendor/` for future GPU deployment. |
| **`llama-server` (Port 8082)** | llama.cpp (C++) | CPU (AMX) | Handles attention and FFN inference for ClarkeYoursaTee GGUF. Implements its own SIMD/AMX matmul internally. |
| **AKLT Tests** | NumPy `matmul` / `dot` | CPU (BLAS) | Uses the BLAS NumPy was built against (OpenBLAS bundled in pip wheels; MKL in conda builds). |
| **C++ Standard Library** | N/A | N/A | C++ does not ship a GEMM. External libraries (Eigen, OpenBLAS) must be explicitly linked. |

## 3. Key Rules for Future Code
* **Do not** write Python inference kernels to override `llama-server`'s C++ attention. The GGUF format and C++ backend are the source of truth for serving.
* **Do not** assume `vendor/DeepGEMM` is running unless the host explicitly has an Nvidia Hopper (H100/H200) GPU.
* **Do** use `numpy.matmul` for CPU-bound tensor tests (like AKLT), but be aware the performance is bound by the underlying OpenBLAS/MKL thread pool, not NumPy itself.
