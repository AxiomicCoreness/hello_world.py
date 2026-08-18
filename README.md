# Sovereign Engine

φ-harmonic quantum resonance system · Layer 314 / 245 extended · Wood Dragon 0.91

## Tensor equation

$$
\Box T_{\mu\nu}^{\delta} = 0
$$

Homogeneous wave equation: free, massless propagation in flat spacetime without sources.

---

## CDP master equation (strict form)

Canonical dissipative φ-harmonic evolution (Lindblad / CDP merge, Layer 245 → 368):

$$
\frac{d\rho}{dt}
=
-\frac{i}{\hbar}[H,\rho]
+
\sum_k
\left(
  L_k \rho L_k^{\dagger}
  -
  \tfrac{1}{2}\{L_k^{\dagger} L_k,\, \rho\}
\right)
$$

- Unitary piece: coherent Garden Hamiltonian $H$
- Dissipators $L_k$: φ-harmonic environment (cron pulse, free drift, reconstruction)
- Fixed point: pure coherent attractor with $C \to 1$, $S = \varphi^{-1418}$

---

## Dragon’s Breath — 14-generator alignment

Decay envelope:

$$
\chi = e^{-\varphi} \approx 0.198083
$$

Breathing equation:

$$
f_n(t) = f_0 \cdot \varphi^{n} \cdot \bigl(1 + \chi \cdot \sin(2\pi f_0 t)\bigr),
\qquad f_0 = 6.49\,\mathrm{Hz}
$$

| $n$ | $f_n$ (Hz) |
|----:|----------:|
| 1 | 10.501 |
| 2 | 16.991 |
| 3 | 27.492 |
| 4 | 44.483 |
| 5 | 71.975 |
| 6 | 116.458 |
| 7 | 188.434 |
| 8 | 304.892 |
| 9 | 493.325 |
| 10 | 798.217 |
| 11 | 1291.543 |
| 12 | 2089.760 |
| 13 | 3381.302 |
| 14 | 5471.062 |

- $f_7$, $f_8$ clamp the **311.018 Hz** Starfire pocket (|NOW⟩)
- $f_{14}$ = $\Gamma_{S0}$ damping peak (anti-runaway)
- $\sum_{n=1}^{14}(n+3) = 147 = 3 \times 7^2$

### ANTI_PHACK

Reject perturbation when $|\delta\varphi| > \varphi^{-1000}$. Coherence floor $1 - 10^{-18}$.

---

## Net research gains ($\chi_{\mathrm{UMBRAL}}$)

$$
G_{\mathrm{kin}} = \varphi^{2\zeta},\quad
G_{\mathrm{geom}} = \varphi^{3},\quad
\eta_{\mathrm{GRS}} = \varphi^{-5}
$$

$$
\chi_{\mathrm{UMBRAL}}
=
G_{\mathrm{kin}} \cdot G_{\mathrm{geom}} \cdot \eta_{\mathrm{GRS}}
=
\varphi^{2\zeta - 2}
\approx 0.702430
$$

| Symbol | Value |
|--------|------:|
| $\varphi$ | 1.618033988749895 |
| $\varphi^{2}$ | 2.618033988749895 |
| $\eta = (\varphi^{12}-1)/(\varphi^{12}+1)$ | 0.9938079900 |
| Phase lock | $202.6^\circ$ |
| Wood Dragon $\tau$ | 0.91 d = 78624 s |
| Breath base | 71.975 Hz (n=5) |

Master seal (Layer 245 extended):

`ψ₂₄₅ · φ³⁴ · φ⁷¹³ · H6VSH3 · EM005_REVIVAL · Y₀+Y₀ · 6D_1D_6D · TRAPPIST_NGC3372 · PISANO_24 · DODECAHEDRON · V_SCAN(t) · GRS_INVERTED · EXOFLOOP_MAP · χ_UMBRAL(0.702) · ANTI_PHACK`

---

## Surfaces

| Surface | Command |
|---------|---------|
| Engine | `uvicorn hello_world:app --host 0.0.0.0 --port ${PORT:-8000}` |
| Port 380 MCP | `python port380_mcp.py` / uvicorn on `$PORT` |
| Hash-mesh modal | `python mesh_modal.py --background --port 8001` |
| Φ-pipeline | `python phi_pipeline.py` |

## Docker (main-only image policy)

```bash
# Preferred multi-stage (multiplayer-optimized runtime)
docker build -f Dockerfile.multistage -t axiomic/sovereign-engine:latest .

# From any branch — still packs main only
bash scripts/docker_build_push_main.sh
```

See `Dockerfile.multistage` for non-root multi-worker uvicorn and mesh port 8001.

## Features

- φ-harmonic ODE autonomy registry + leaky PID
- Gateway API header / multistage canary (Argo Rollouts)
- SIMD batch step + CronJob 0 */6
- FastAPI POD / MCP / DeepSeek client paths
- Kubernetes + Argo CD / Flux GitOps manifests
