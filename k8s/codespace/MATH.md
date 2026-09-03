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
