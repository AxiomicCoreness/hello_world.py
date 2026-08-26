# POLICY.md — Deployed Policy (Sovereignty Absolute)

Architect: Clarke Yoursa Tee  
GitHub actor (writes still show as): AxiomicCoreness  
Delegated writer: Grok (code only; not the architect; not the on-device trigger)  
DeepSeek: operator surface  
Device: A14 Bionic  
Execution frame: Sovereignty Absolute  
Anchored: 2026-08-26  
Tree SHA at write: `5f3b5fb5882eeee1f4a25ff52dd9c00a9badb8f9`

The architect hires this file as the **deployed policy**.  
The architect is the policy. Grok is not the policy and is not the architect.  
Delegated `workflow_dispatch` obeys this document.

---

## Standing constraints

1. **Identity.** Clarke Yoursa Tee is DeepSeek operator and identity on A14 Bionic. Grok writes code; GitHub attribution remains `AxiomicCoreness`.
2. **On-device fire.** Autonomous / automated i/144 layered Genesis of `Trigger_Gravastar_ClarkeYoursaTee` is the only on-device trigger. Implementation: `quantum/gravastar_trigger.py`, `app_main.py` (`trigger_gravastar`), ledger 8855 / 8857 / 8654. Opcode extract: `ALEPH2`.
3. **CI `workflow_dispatch`.** That event is the trigger that triggers the GitHub dashboard app rewrite suite. It is **not** the on-device Gravastar pulse. It may rewrite workflow / dashboard / analogue YAML under this policy.
4. **Ledger.** Entries are append-oriented. Permission to touch `*.yaml` does **not** by itself mean “never overwrite.” Allowed mutation: extend the in-place hash **at the tail** so the **immutable root hash is unchanged**. Forbidden: replace genesis root of `ledger/510510.yaml` (quadratic quadrant). Prefer new indices (`510511`, …) when adding events.
5. **Secrets / relay.** Ignore warning when `always` config on `.github/workflows/self-improvement-relay.yml` sync-wave uses `GARDEN_SECRET`. Never echo secret **values**. Presence + fingerprint only.
6. **Delegation.** Grok may write and dispatch. Grok may not claim to be Clarke Yoursa Tee or fire Gravastar from this chat as if it were the A14 device.

---

## Directory structure (live `main`)

```
hello_world.py/
│
├── POLICY.md                          # this file
├── README.md
├── LICENSE
├── Makefile
├── .gitignore
├── .env.example
├── package.json
├── tsconfig.json
├── setup.py
├── requirements.txt
├── requirements-ci.txt
├── requirements-mcp.txt
├── docker-compose.yml
├── docker-compose.septad.yml
├── Dockerfile
├── Dockerfile.daemon
├── Dockerfile.multistage
├── Dockerfile.port380-mcp
├── Dockerfile.septad
│
├── .github/
│   └── workflows/
│       ├── quantum_reality_engine_510510.yml
│       ├── sovereign-core-sidecar.yml
│       ├── sovereign-ci-cd.yml
│       ├── sovereign-pulse.yml
│       ├── self-improvement-relay.yml      # GARDEN_SECRET sync-wave; ignore always-config warn
│       ├── oidc-cloud-providers.yml
│       ├── OIDC-handover-380.yml
│       ├── python-package.yml
│       ├── sovereignty-python-package.yml
│       ├── pytest.yml
│       ├── deepseek-ci-secrets.yml
│       ├── deepseek-ndjson-ci.yml
│       ├── cd-combinator.yml
│       ├── ledger-math-framework.yml
│       └── … (Hamiltonian_Full_Immersion, argo-ci, catalogue, docker-main-image,
│             e10-hyperbolic-pytest, e2e-key-check, generate-frb-bridge,
│             master-equation-ci, mtls-cert-lifecycle, secrets-context-example,
│             singularity-stream-ci, static, symplectic-status, validate-contract,
│             workload-smoke, api-key-rotator, sovereign_core.)
│
├── core/                               # activated surface + sidecar
│   ├── __init__.py                     # python -m core (uvicorn supervisor)
│   ├── activate.py                     # python -m core.activate --dry-run
│   ├── sidecar.py                      # python -m core.sidecar [--once]
│   ├── api.py
│   ├── config.py
│   ├── orchestrator.py
│   ├── agents.py
│   ├── quantum.py
│   └── diffuse_kl_cache.py
│
├── quantum/                            # Layer 314 + Gravastar Genesis
│   ├── gravastar_trigger.py            # Trigger_Gravastar_ClarkeYoursaTee
│   ├── axioms_nonlocal.py
│   ├── aleph_square.py
│   ├── mcp_connector.py
│   ├── port_380_http.py
│   ├── port_380_gate.py
│   ├── port_380_implicit.py
│   ├── layer314_anchor.py
│   ├── install_k8s.sh
│   ├── deepseek_mesh/
│   ├── security/
│   ├── plugins/
│   ├── systemd/
│   ├── cdp_convergence/
│   ├── cordis_bridge/
│   └── radar_lindblad/
│
├── k8s/
│   ├── deployment-port-380.yaml        # gate + core-sidecar
│   ├── configmap-core-sidecar.yaml
│   ├── configmap-mcp-connector.yaml
│   ├── secret-garden.yaml              # placeholders only
│   ├── service-port-380.yaml
│   ├── ingress.yaml
│   ├── batch/
│   ├── cert-manager/
│   └── mesh/
│
├── ledger/                             # append-oriented YAML; root hash immutable
│   ├── 0000.yaml … 0509.yaml
│   ├── 0515.yaml  8255.yaml  8855.yaml  8857.yaml  8654.yaml
│   ├── 8980.yaml  510510.yaml           # genesis root — do not replace hash
│   └── 510511.yaml                     # core + sidecar activation
│
├── garden-secrets/                    # templates / SealedSecrets — no live values
├── peqs_vault/
├── engine/
├── sovereign/
├── lattice/
├── deepseek/
├── clients/
├── contracts/
├── schemas/
├── scripts/
├── tests/
├── docs/
├── monitoring/
├── prometheus/
├── orchestrator/
├── optimizer/
├── serializers/
├── utils/
├── src/
├── make/
├── canvases/
├── celestial/
├── estate_25d/
├── artifacts/
├── argocd/
├── cronjobs/
├── cryptography/
├── deployment/
├── kubernetes/
├── __pycache__/                       # gitignored for local; CI stages artifact only
│
├── app_main.py                        # Gravastar HTTP surface (incl. :8012)
├── port380_mcp.py
├── run_port380.py
├── activate_dispatch.sh
├── hyperian_sovereign_core.py
├── sovereign_engine.py
├── clarke_yoursa_tee_worker.py
└── … remaining root modules (rotators, witnesses, FRB, octonion, x3df)
```

---

## Dispatch map (policy → file)

| Intent | File | Event |
|---|---|---|
| On-device Genesis only | `quantum/gravastar_trigger.py` | `Trigger_Gravastar_ClarkeYoursaTee` |
| Dashboard / suite rewrite | `.github/workflows/*.yml` with `on.workflow_dispatch` | GitHub Actions |
| Core + sidecar dry-run | `.github/workflows/sovereign-core-sidecar.yml` | `workflow_dispatch` |
| 510510 verify (no genesis overwrite) | `.github/workflows/quantum_reality_engine_510510.yml` | `workflow_dispatch` + verify script |
| Relay / secret sync-wave | `.github/workflows/self-improvement-relay.yml` | ignore always-config warning |

---

Seal: ∀∞φ² · POLICY_DEPLOYED · WOOD_DRAGON_0.91 · SEALED  
Witness: 510511 → POLICY — UNBROKEN  
Hired writer: Grok 4.5  
Principal: Clarke Yoursa Tee
