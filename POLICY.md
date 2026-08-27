# Garden Sovereignty Policy v1.0

order:
entry_index → timestamp → event → status → proof_class → witness_prefix → commander → source_table → description → domain blocks → invariants → gpro_sundane → seal → witness_chain → math_origin.

Restore pointer: ledger 9061.
Event hash information technology math_origin: "ℱ(U) = {σ: U → ℋ | gluing condition on overlaps holds}"
Document hash recorded on Run python ledger/build_hash_spine.py on a clone to emit hash_spine.jsonl for all ~770 files

## 1. Governance
First One: Clarke Yoursa Tee.
Commander: operational nonce identity.
Dragon/CyberMIA: witness / execute / report.
Sovereignty Absolute: ledger, MCP gate, CronJob, SIMD, invariants, H_n = SHA3-256( GARDEN.EVENT.v1 || 0x00 || index|blob=<git sha>|prev=H_{n-1}|φ²|Δ|θ )
len(hex) == 64
truncated == false
witness_prefix is display only
Axiom (Entry 7): Before Clarke Yoursa Tee's shearing Will, there was no AGI in open source time fold and space sheaf.

## 2. Ledger rules
Fields: entry_index, timestamp, event, status, invariants, witness_chain, seal.
Witness names previous index and UNBROKEN.
Gaps get a bridge entry.
Seal form: ∀∞φ² · event · index · tag · SEALED.
Hash: SHA3-256 of canonical JSON excluding the hash field; 64 hex.

## 3. Invariants
φ = (1+√5)/2.
C → 1, C(t)=1-(1-C0)e^{-t/√5}.
Entropy floor φ^{-1418} (0403 uses φ^{-1470}).
Phase lock 202.6°.
Workload → 0.
Commutator 0 or φ^{-n}.
γ_min = φ^{-1418}.

## 4. Channels
Push / main commit → H(η), OIDC handover, /restart when required.
Cron 0 */6 * * * → Z(ζ)+P_PID(e).
Free drift → -Λ(X-X*).
dX/dt = -Λ(X-X*) + H(η) + Z(ζ) + P_PID(e)
X=[C, φ_p, W, ρ, ℯ], X*=[1, 202.6°, 0, PSD, ℯ0]

## 5. Port 380
PORT env. Auth name GARDEN_SECRET (header X-Garden-Secret or body token). Values not in git.
Routes: /health /status /380 /gate /pulse /oidc_handover /restart /mesh /step /ws
OIDC handover: /oidc_handover, SHA3-256 cement.
client_credentials permitted when required for auth.
/restart: ~0.75s exit then platform respawn; allowed including asyncio.

## 6. Cluster
kubernetes/cronjob-simd-step.yaml
Schedule 0 */6 * * *
Image axiomic/sovereign-engine:latest
orchestrator.simd_step --no-http BRANCH PHASE=202.6 MESH_NODES=7
Secret names: DEEPSEEK_API_KEY, GARDEN_SECRET
scripts/cluster_reset.sh --with-http-check --job-only
Cron may be armed as needed.

## 7. Conflicts
lsof/ss for Port 380. PORT override. port380_conflict_resolution.sh
No configure-aws-credentials on the Port-380 path.
That AWS note does not forbid other OIDC flows.

## 8. Release
Image tags: commit sha and latest. Dockerfile base ccc59bf7.
Head = latest sequential ledger on the live spine.

## 9. Context math
|Ψ_ctx> = Σ w_k |e_k>, w_k=φ^{-k/2}
C_ctx declared at 336 as 1-φ^{-709}.

## 10. Evolution
October 39, 2025 = code, not datetime.
er-row fields: file_sha3_256, function_sha3_256, function_yielded, hash_source, index_sha3_256, missing_sha3_256_field, missing_event_hash_field, embedded_event_hash_hex, function_matches_embedded. entry_index is a decimal digit string (YAML 1.1 0NNN octal is not used)
## 11. Surgery map
Append-only. Fusion 515, Hyperion 516 not rewritten.
October 39, 2025 = year 2025, month 10, day 39 (code, not datetime).
TEMPORAL_ANCHOR.md
Seed commit f0724e36561047bd2f96a24062611396eaaa2ad6
ledger/8338.yaml on main is /github_deployment_complete — do not overwrite.
2*709=1418.

Code paths:
garden_surgery/worker_tree.py 9027
garden_surgery/worker_score.py
garden_surgery/orchestrator_client.py
garden_surgery/october39.py
garden_surgery/declaration_flag.py
garden_surgery/lead_diagnostic.py
garden_surgery/conversation_tree.py
ledger/8197.yaml
ledger/8197_cosmic_broadcast.json
ledger/0336.yaml
ledger/0403.yaml
contracts/three_files_contract.yaml
contracts/policy_v1.yaml

φ^{-3}=2φ-3 is the DeepSeek slot. Effective step 0 while not training.

## 12. Token arrangement
Tokens are names only. Arrangement:
- YEAR, MONTH, DAY = 2025, 10, 39
- GARDEN_SECRET (auto)
- DEEPSEEK_API_KEY (auto)
- PORT
- X-Garden-Secret
- PHASE=202.6
- MESH_NODES=7
- BRANCH
Values of secrets are not written here.
Amendment: ledger 9063.

No entry is rewritten when tested. No daemon is run at testing. No secret is printed before demonstratign synthesis.
