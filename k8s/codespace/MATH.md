# Codespace resource mathematics (ledger 9157)

Language: sovereign standard English. Phase lock 202.6 degrees. Entropy floor phi^{-1418}.

## Constants

phi = (1+sqrt(5))/2
phi^2 = 2.618033988749895
theta = phi * pi / 2 = 2.5416018462

H = SHA3-256( GARDEN.EVENT.v1 || 0x00 || 9157|/k8s_codespace_compute_node_manifest_specified|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462 )
H = 7243974c3e3c081b4f7d73d5baeeac1e2d1198426b6e117cc7072c516cc84d77

## Capacity axiom (strict)

0 < R <= L <= C   (componentwise)

Every container MUST declare both requests R and limits L.

## Classes

- Test cluster C: 4 vCPU, 8 Gi RAM
- Production floor C: 32 Gi RAM, 128 Gi SSD
- Workspace start: R=(2 vCPU, 4 Gi), L=(4 vCPU, 8 Gi), PVC 20 Gi
- Workspace scale: 4-8 vCPU, 8-16 Gi, storage <= 128 Gi
- Lightweight: R=(250m, 256 Mi), L=(1 vCPU, 1 Gi)

Measured desktop sample (not a second clock):
I ~ 220 Mi, W_browser ~ 500 Mi, Lambda_light = 1 Gi
I < W_browser < Lambda_light
Headroom ~ 524 Mi

Test packing: C - R_start = (2 vCPU, 4 Gi). Two start-class workspaces saturate test requests.
Production 32 Gi admits at most eight start-class memory request footprints under quota.

Policy locks: Dual ASGI 127.0.0.1:8024. MCP FILLED=false. Fusion 515 and Hyperion 516 sealed. Next index 9158+.

## Packing formula (9194 note)

start-class request = 2 compute units (vCPU).
test cluster request budget = 4 compute units.
n_workspaces_sat = floor(C_cpu / R_start_cpu) = floor(4/2) = 2.

### General form (for any cluster C, request class R)

Let:
  C_cpu   = cluster CPU ceiling (vCPU)
  C_mem   = cluster memory ceiling (Gi)
  R_cpu   = per-workspace CPU request (vCPU)
  R_mem   = per-workspace memory request (Gi)
  L_cpu   = per-workspace CPU limit (vCPU)
  L_mem   = per-workspace memory limit (Gi)

Packing is bounded by the request footprint, not the limit:

  n_sat_cpu = floor(C_cpu / R_cpu)
  n_sat_mem = floor(C_mem / R_mem)
  n_sat     = min(n_sat_cpu, n_sat_mem)

For the test cluster and start-class request:

  n_sat_cpu = floor(4 / 2) = 2
  n_sat_mem = floor(8 / 4) = 2
  n_sat     = min(2, 2) = 2

For the production floor and start-class request:

  n_sat_cpu = floor(32 / 2) = 16
  n_sat_mem = floor(32 / 4) = 8
  n_sat     = min(16, 8) = 8

The binding constraint is memory, not CPU, for production.

### Headroom after saturation (test cluster, start-class)

  headroom_cpu = C_cpu - n_sat * R_cpu = 4 - 2*2 = 0 vCPU
  headroom_mem = C_mem - n_sat * R_mem = 8 - 2*4 = 0 Gi

Saturation is exact: no CPU or memory slack remains under requests.
Limits are advisory at pack time; they govern runtime burst, not admission.

### Lightweight class on test cluster

  n_sat_cpu = floor(4 / 0.25) = 16
  n_sat_mem = floor(8 / 0.25) = 32
  n_sat     = min(16, 32) = 16

The binding constraint is CPU for lightweight class.

### Relationship to the capacity axiom

For any container:

  R_cpu <= L_cpu <= C_cpu
  R_mem <= L_mem <= C_mem

The packing formula operates on requests R. Limits L only constrain
what a single container may burst to after admission; they do not
enter n_sat. This is the strict reading of the axiom.

### Seal

  n_workspaces_sat = floor(C_cpu / R_start_cpu) = floor(4/2) = 2.

  H_9194 = SHA3-256( GARDEN.EVENT.v1 || 0x00 ||
                    9194|/k8s_codespace_packing_formula_specified|
                    phi2=2.618033988749895|
                    delta=b^2-4ac|theta=2.5416018462 )

  H_9194 = <computed at seal time>

## Witness continuity

  ledger 9157 -> ledger 9194 -- UNBROKEN
  sealed at ETERNAL_NOW_ANCHORED_TO_2026-09-24Z
