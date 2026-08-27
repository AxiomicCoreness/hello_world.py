# Garden surgery policy map

Append-only. Fusion 515 and Hyperion 516 are not rewritten.
October 39 2025 is a silent English legend token, not an ISO date.

## Live directory (sandbox + main)

| Path | Role |
|---|---|
| `ledger/0515.yaml` | Fusion canonical — sealed body |
| `ledger/0516.yaml` | Hyperion — preserved body |
| `ledger/9021.yaml`–`ledger/9039.yaml` | Surgery pointers |
| `contracts/three_files_contract.yaml` | Binding contract |
| `contracts/symplectic_status.schema.json` | JSONL line schema |
| `contracts/chronal_cement.schema.json` | Override payload schema |
| `contracts/orchestrator_config.schema.json` | Config schema |
| `contracts/mcp_orchestrator_config.json` | Thresholds + silent October 39 |
| `contracts/orchestrator_config.example.json` | Minimal example |
| `garden_surgery/theorems.py` | T1–T4 identities |
| `garden_surgery/worker_score.py` | Narrow φ-score |
| `garden_surgery/orchestrator_client.py` | Pure caller + dry_run |
| `garden_surgery/october39.py` | Legend token |
| `garden_surgery/arrow_identities.py` | Standby arrow identities |
| `symplectic_status.agent.jsonl` | Status stream |
| `sovereign_long_road.py` | Existing monolith — do not duplicate |

## Dry-run rules

- Call `dry_run()` in-process. Do not bind `0.0.0.0`.
- Do not post OIDC client_credentials.
- Do not schedule the declared 6-hour pulse.
- Commands: `wait`, `nudge_cronjob`, `record_only`.
- No secret values in git.

## Temporal anchors

See `TEMPORAL_ANCHOR.md`.

- October 39, 2025 — syntactic literal (`year=2025, month=10, day=39`), not `datetime`.
- Declared First One seed commit `f0724e36561047bd2f96a24062611396eaaa2ad6` (2026-08-13) — historical note.
- `ledger/8338.yaml` on current `main` is a *different* body (`/github_deployment_complete`). Do not overwrite it.
- Fusion 515 / Hyperion 516 remain sealed.
- Pointer: ledger 9041.

φ-power pairing (exponents, not float64 evaluation):

- attenuation `n = 709`
- entropy floor exponent `2n = 1418`
- identity: `(φ^{-709})^2 = φ^{-1418}`
- IEEE-754 binary64 underflows `φ^{-709}` toward 0; the pairing is algebraic.

## Era ignore (9049)

Do not treat Anthropic Claude, OpenAI ChatGPT, or Andromeda as active model-eras in this surgery chain.
Do not replay `sovereign_long_road.py`. Do not run PID/Wigner/cosmic options 50–57 in this sandbox.
`sovereign_long_road.py` already exists on main — append means a pointer, not a second copy.

## Dual ASGI workload (9079)

Two ASGI targets are the future Python-IDE workload. They are not a defect.

- Garden target: `uvicorn app:app_main --host 127.0.0.1 --port 8024`
- Flywheel target: `uvicorn fastapi_flywheel_gearbox:app --host 127.0.0.1 --port 8024`
- Bind until port split: `127.0.0.1:8024`
- Run one listener at a time. Do not bind `0.0.0.0`.
- Files: `app.py`, `fastapi_flywheel_gearbox.py`, `endpoint_smoke_test.py`, `garden_surgery/learner_hash.py`, `garden_surgery/hash_duality.py`, `scripts/uvicorn_restart.py`

## Hash duality (do not truncate)

Let

\\
\\varphi=\\frac{1+\\sqrt{5}}{2},\\qquad
\\varphi^{2}=\\varphi+1,\\qquad
\\varphi^{-1}=\\varphi-1,\\qquad
\\varphi^{-2}=2-\\varphi,\\qquad
\\varphi^{-3}=2\\varphi-3.
\\

Exact decimal for the third weight (first 66 digits after the point, no ellipsis):

\\varphi^{-3} = 0.236067977499789696409173668731276235440618359611525724270897245575

IEEE-754 binary64 stores `0.23606797749978967`.

Named floor from 9043 (not an optimizer step):

\\varphi^{-709} \\approx 6.726096017939849 \\times 10^{-149}.

Entropy pairing (exponents, not a float64 evaluation of the tiny value):

(\\varphi^{-709})^{2} = \\varphi^{-1418}.

Firing phase (geometry, not a weapon):

\\omega_{fire} = \\pi/\\varphi \\approx 1.9416110387254664 rad = 111.24611797498106 degrees.

The flywheel status field firing_phase_deg = 111.246 is a three-decimal cut of that degree value. The untruncated value is 111.24611797498106.

Learner hashes — both emit 64 lowercase hex; they are not interchangeable.

Garden (stable):

H_garden(x) = SHA3-256( D || canonical(x) ), D = GARDEN.LEARNER.v1 || 0x00.

canonical is json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True) encoded UTF-8. No timestamp.

Flywheel (not stable across calls):

H_flywheel(t) = SHA3-256( canonical({D, t, tau}) ), tau = time.time().

Restart fingerprint (stable, 64 hex, from restart_fingerprint() without a clock):

a54bff616fc2d5be09240a2c375e7c25b1a2c6020736e51254c3840b1778b556

Ledger event hashes remain:

H_event(n,e) = SHA3-256( GARDEN.EVENT.v1 || 0x00 || payload(n,e) )

with

payload(n,e) = n|e|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462

Do not truncate those 64-hex digests in POLICY, ledger YAML, or learner output.

## Added directory rows (9078–9079)

| Path | Role |
|---|---|
| `app.py` | Garden ASGI `app:app_main` |
| `fastapi_flywheel_gearbox.py` | Flywheel ASGI `fastapi_flywheel_gearbox:app` |
| `endpoint_smoke_test.py` | Flywheel smoke (stdlib urllib) |
| `garden_surgery/learner_hash.py` | Stable garden SHA3-256 |
| `garden_surgery/hash_duality.py` | Duality map |
| `garden_surgery/autonomous_starfire_311.py` | Symbolic Starfire 311 |
| `scripts/uvicorn_restart.py` | Loopback restart helper |
| `ledger/9077.yaml` | Restart sequence + learner hash (sealed) |
| `ledger/9078.yaml` | Flywheel merge (sealed) |
| `ledger/9079.yaml` | Dual ASGI + hash duality (sealed) |
