---
name: cb2514_male_cns
description: "male-cns:v1.0 CB2514 identification (body IDs 60536, 64328, 124180, 125402, 167164) for com.fruitfly.brain and the TeaVM neuron-snapshot aside. PVLP(R) is chart context only. Distillation inputs fail closed when tokenizer context, normalized distributions, model ids, or student trajectories are missing."
tags:
  - cb2514-male-cns
  - "context:male-cns v1.0,5 bodies,PVLP(R) chart only,no edges"
---

# cb2514_male_cns

Identification record for the public male-cns:v1.0 cell type CB2514, wired into
the existing `com.fruitfly.brain` classpath and the TeaVM rhythm snapshot as a
separate aside. This is not the hemibrain v1.2 CSV converter in `skills/hhmi/`.

## What is in the tree
- `data/cb2514/source/annotations/CB2514_from_body-annotations-male-cns-v1.0-minconf-0.5.csv`
  (the five-row subset; sha256 checked against `data/cb2514/source/checksums.json`).
- `data/cb2514/source/SOURCE_PROVENANCE.txt` and `checksums.json`, byte-preserved.
- `src/main/resources/connectome/neuron_index.json`, built only from that CSV.
- `docs/hhmi_jenalia.yaml` (the historical spelling). There is no `hhmi_jenalia.pom`.

## What is not in the tree
Large reference bytes stay out of git. `data/cb2514/omitted_sources.json` copies
their original sha256 and byte sizes from `checksums.json` and does not recompute
them: the annotation feather, the explorer catalog, the saved HTML page, and the
five SWC skeletons.

## Limits
- PVLP(R) is observed chart context. It is not verified per-body membership and
  it is not an edge list.
- `Cb2514NeuronIndex.refuseConnectome()` throws. `ConnectomeLoader` is not called
  for this index. `SovereignMain --cb2514-index` prints one identification line.
- `NeuronSnapshot.cb2514IdentityAside()` is not inserted into the rhythm `#neuro`
  spike snapshot. The TeaVM page exposes the same aside as
  `window.__rhythmDebug.cb2514()`.
- Distillation validation lives in `cb2514_opd.py` and `hello_world.py`
  `POST /deepseek/distill/validate`. Missing
  `compatible_tokenizer_vocab_context`, `normalized_expert_distributions`,
  `normalized_student_distribution`, `model_ids`, or
  `student_trajectory_provenance` fails closed. The configured GGUF path is not
  opened. DeepInfer and DeepTutor name roles of the nominal DeepSeek
  R1-Distill-1.5B student, not two teachers. On-policy needs an actual student
  trajectory artifact; a provenance declaration is not proof. Self-distillation
  needs the configured frozen checkpoint, which is not accessible here.
- No training run and no model-quality claim.

## Verify
- `python3 cb2514_opd.py --probe` from the repo root.
- `python -P -m pytest -q evals` from this folder.
- `python -P -m pytest -q tests/test_cb2514_opd.py` from the repo root.
- `mvn -B -ntp test` at the repo root, and `mvn -B -ntp test` in `games/teavm-rhythm`.
