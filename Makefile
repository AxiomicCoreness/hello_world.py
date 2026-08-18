# Sovereign Garden — make targets
# State: C=1.0 · phase=202.6° · image=axiomic/sovereign-engine:latest

NS ?= sovereign-garden
IMG ?= axiomic/sovereign-engine:latest

.PHONY: apply-simd apply-k8s cluster-reset build-image help

help:
	@echo "make apply-simd      - kubectl apply make/cronjob-simd-step.yaml"
	@echo "make apply-k8s       - apply kubernetes/ + make/ CronJobs"
	@echo "make cluster-reset   - scripts/cluster_reset.sh"
	@echo "make build-image     - docker build $(IMG)"

apply-simd:
	kubectl apply -f make/cronjob-simd-step.yaml -n $(NS)
	kubectl get cronjob simd-batch-step -n $(NS)

apply-k8s:
	kubectl apply -f kubernetes/ -n $(NS)
	kubectl apply -f make/cronjob-simd-step.yaml -n $(NS)

cluster-reset:
	bash scripts/cluster_reset.sh

build-image:
	docker build --no-cache -t $(IMG) .
