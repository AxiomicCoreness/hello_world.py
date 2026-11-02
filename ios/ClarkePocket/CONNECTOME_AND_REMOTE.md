<!-- SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com> -->
<!-- SPDX-License-Identifier: MIT -->
# Clarke Pocket: connectome panel and PC-side Ray/CUDA backend

Both live in the **Model** tab (`ClarkePocket/ConnectomeRemoteViews.swift`), with the logic in
`Sources/PocketCore/Connectome.swift` and `Sources/PocketCore/RemoteCompute.swift`, unit-tested in
`Tests/PocketCoreTests/ConnectomeAndRemoteTests.swift` (offline, no sockets).

## Connectome: `HHMIJaneliaMap.xml` (placeholder)

- `HHMIJaneliaMap.xml` is a **placeholder**: a hand-written 3-neuron ring (A → B → C → A, weights
  1.0 / 0.8 / 0.5). It is **not** HHMI Janelia FlyEM hemibrain data. The app shows it under the
  title *CONNECTOME (PLACEHOLDER)* and names it only as
  “HHMIJaneliaMap.xml (placeholder: hand-written 3-neuron ring, NOT HHMI Janelia FlyEM hemibrain data)”.
- The app bundles `ClarkePocket/Resources/HHMIJaneliaMap.xml`, a byte-identical copy of the
  placeholder at `src/main/resources/HHMIJaneliaMap.xml` (the file `com.fruitfly.brain.ConnectomeLoader`
  reads). A test fails if the two ever differ.
- **Run simulation** runs a small, deterministic leaky integrate-and-fire model over the placeholder
  map and is labelled “Simulation … not recorded neural data”. On the placeholder it shows A, B, C
  firing once and the wave stopping (C → A is 0.5, below the 0.75 threshold).
- Not wired: the repo has no SQLite connectome tables. PR #171's SQLite backend stores **chat
  history** (`sovereign-irc-bridge/src/llm_history_sqlite.py`), not neurons or synapses.

## PC-side Ray/CUDA backend (remote, off by default)

- iOS has no CUDA. Nothing CUDA-related runs on the iPhone, and nothing pretends to.
- The option is listed as “PC-side Ray/CUDA (remote: runs on your PC, never on the iPhone)”, **off by
  default** (`rayCudaRemoteEnabled`). When on, the only thing the app does is
  `GET http://127.0.0.1:<port>/healthz` (default port 8095) and show the answer. Endpoints other than
  `http://127.0.0.1:<port>` are refused (not `localhost`, not `0.0.0.0`, not a LAN address).
  127.0.0.1 is the device itself: it reaches the PC from the iOS Simulator on that PC, or through a
  forwarded port.
- Expected answer (the contract this client implements):
  `{"backend":"ray-cuda","cuda_available":true,"ray_workers":4,"simulated":false}`.
  An answer with `"simulated": true` is always shown as a **SIMULATION**.
- **Chat never routes to it.** On-device llama.cpp and the opt-in PC bot over IRC remain the only
  ways an answer is produced.
- What exists in the repo today: `multibody_simulator/unified_cuda_mesh_ray.py` (JAX + torch.distributed;
  despite its name it does not import Ray) and the `vendor/DeepGEMM`, `vendor/DeepEP`, `vendor/FlashMLA`,
  `vendor/DeepInfer` gitlinks (third-party deepseek-ai submodules). There is **no** PC-side service that
  answers `/healthz` yet, so the check reports “not reachable” until one is written and bound to 127.0.0.1.
  Tests use `StubRayCUDARemote`, which always reports itself as simulated.
