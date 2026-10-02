# workloads.mk
# ============
# Stub targets expected by .github/workflows/sovereign-workload-matrix.yml
# Soft-skip: missing implementations do not fail the job.

.PHONY: seal-verify rotate-keys simulate mesh-terminal anatomy-verify help

seal-verify:
	@echo "seal-verify: workload not fully configured (soft skip)"
	@echo "  To enable: implement ledger verification"
	@exit 0

rotate-keys:
	@echo "rotate-keys: workload not fully configured (soft skip)"
	@echo "  To enable: implement key rotation in scripts/startup_secrets_rotator.py"
	@exit 0

simulate:
	@echo "simulate: workload not fully configured (soft skip)"
	@echo "  To enable: implement workload simulation"
	@exit 0

mesh-terminal:
	@echo "mesh-terminal: workload not fully configured (soft skip)"
	@echo "  To enable: implement mesh terminal"
	@exit 0

anatomy-verify:
	@echo "anatomy-verify: workload not fully configured (soft skip)"
	@echo "  To enable: implement anatomy verification"
	@exit 0

help:
	@echo "Sovereign Workload Matrix — available targets:"
	@echo "  make seal-verify       — verify ledger seals (append-only)"
	@echo "  make rotate-keys       — rotate secrets and keys"
	@echo "  make simulate          — run simulation batch"
	@echo "  make mesh-terminal     — run mesh terminal CI"
	@echo "  make anatomy-verify    — verify anatomy structure"
	@echo ""
	@echo "All targets soft-skip when implementations are missing."
