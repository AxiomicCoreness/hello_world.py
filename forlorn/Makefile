# ClarkeYoursaTee: build / eval / seal / serve. Loopback only; no weights in git.
GGUF_PY  ?= python3
PYTHON   ?= python3
MODEL    ?= /workspace/llama/ClarkeYoursaTee-1.5B-Q4_K_M.gguf
EVAL_URL ?= http://127.0.0.1:8082/v1/chat/completions
EVALS    := eval_ledger_syntax eval_math_drift eval_hallucination_rate

.PHONY: build eval seal serve

build:
	OUT=$(MODEL) GGUF_PY=$(GGUF_PY) bash ./build_gguf.sh

# Gate: every eval must pass; make stops at the first failing eval.
eval:
	@set -e; for e in $(EVALS); do $(PYTHON) skills/evaluation/$$e.py --url $(EVAL_URL); done

# Verify the built GGUF against MANIFEST.json (prints sha256 + SHA3-256). Never edits the ledger.
seal:
	$(PYTHON) ledger_integration/seal_model_hash.py $(MODEL) --check MANIFEST.json

serve:
	MODEL=$(MODEL) bash ./serving/launch_8082.sh
