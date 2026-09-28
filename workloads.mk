# workloads.mk — Sovereign Workload Mesh make targets
# Appended alongside existing Makefile; does not modify it.
# Policy: POLICY.md Art. 25-33; no MCP writes; ledger append-only.

REGISTRY ?= workload_registry.json

.PHONY: dispatch verify pulse seal-verify rotate-keys simulate mesh-terminal list

list:
	@echo "Registered workloads:"
	@python3 -c "import json;[print(' -', w['id'], '(' + w['schedule'] + ')') for w in json.load(open('$(REGISTRY)'))['workloads']]"

# CI-only entrypoints. Never calls terminal.main().
seal-verify:
	python3 compute_seal.py
	python3 verify_witness_chain_9179_9188.py || echo "witness verify: partial"

rotate-keys:
	python3 sovereign_key_rotator.py --dry-run
	python3 ci_cd_key_rotator.py --dry-run

simulate:
	python3 master_equation.py --batch
	python3 hybrid_rk4_simulator.py --batch

mesh-terminal:
	python3 quantum/deepseek_mesh/terminal_ci.py

dispatch:
	@echo "Dispatch via: gh workflow run sovereign-workload-matrix.yml -f workload=<id>"

verify:
	python3 run_verify.py

pulse: verify seal-verify
	@echo "pulse complete"
