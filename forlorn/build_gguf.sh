#!/usr/bin/env bash
# Build ClarkeYoursaTee-1.5B-Q4_K_M.gguf: a metadata-only derivative of the
# abliterated Qwen2.5-1.5B-Instruct GGUF. Tensors are copied byte for byte;
# only general.name, general.description and the chat template change.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="${BASE:-/workspace/llama/Qwen2.5-1.5B-Instruct-abliterated.Q4_K_M.gguf}"
OUT="${OUT:-/workspace/llama/ClarkeYoursaTee-1.5B-Q4_K_M.gguf}"
GGUF_PY="${GGUF_PY:-python3}"          # a Python with `pip install gguf==0.19.0`
BASE_SHA256=59aa9f44bde5349dbe292d7024d197db605f422b8baf65f3246a59abbde4e8e9
BUILD="$HERE/build"
mkdir -p "$BUILD"

echo "[build] verifying base $BASE"
got="$(sha256sum "$BASE" | cut -d' ' -f1)"
if [ "$got" != "$BASE_SHA256" ]; then
  echo "FATAL: base sha256 $got != pinned $BASE_SHA256" >&2; exit 1
fi

# Bake the default system prompt and few-shot turns into the base template's
# default-system branch. They apply only when a client sends no system message;
# the /llm bridge always sends its own, so bridge turns are unaffected.
"$GGUF_PY" - "$BASE" "$HERE/system_prompt.txt" "$HERE/fewshot.json" "$BUILD/chat_template.jinja" <<'PY'
import json, sys, gguf
base, prompt_file, shots_file, out = sys.argv[1:]
r = gguf.GGUFReader(base)
f = r.fields["tokenizer.chat_template"]
tpl = bytes(f.parts[f.data[0]]).decode()
prompt = open(prompt_file, encoding="utf-8").read().strip()
shots = json.load(open(shots_file, encoding="utf-8"))["shots"]
if not all(isinstance(p, list) and len(p) == 2 and all(isinstance(t, str) and t for t in p) for p in shots):
    sys.exit("FATAL: every shot must be a [user, assistant] pair of non-empty strings")
texts = [prompt] + [t for pair in shots for t in pair]
if any(("'" in t) or ("\\" in t) for t in texts):
    sys.exit("FATAL: prompt and shots must not contain single quotes or backslashes (jinja '...' literals)")
esc = lambda t: t.replace("\n", "\\n")
qwen = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
no_tools = "{{- '<|im_start|>system\\n" + qwen + "<|im_end|>\\n' }}"
if tpl.count(qwen) != 2 or tpl.count(no_tools) != 1:
    sys.exit("FATAL: base template does not have the expected Qwen default system lines")
turns = "".join(f"<|im_start|>user\\n{esc(u)}<|im_end|>\\n<|im_start|>assistant\\n{esc(a)}<|im_end|>\\n"
                for u, a in shots)
tpl = tpl.replace(no_tools, "{{- '<|im_start|>system\\n" + esc(prompt) + "<|im_end|>\\n" + turns + "' }}")
tpl = tpl.replace(qwen, esc(prompt))  # tools branch: system text only
open(out, "w", encoding="utf-8").write(tpl)
PY

DESC="ClarkeYoursaTee 1.5B Q4_K_M. Metadata-only derivative of huihui-ai/Qwen2.5-1.5B-Instruct-abliterated (base Qwen/Qwen2.5-1.5B-Instruct), from the mradermacher/Qwen2.5-1.5B-Instruct-abliterated-GGUF Q4_K_M file sha256 $BASE_SHA256. Weights unchanged; general.name, default system prompt and default few-shot turns changed. Not fine-tuned."
"$GGUF_PY" -m gguf.scripts.gguf_new_metadata --force \
  --general-name ClarkeYoursaTee \
  --general-description "$DESC" \
  --chat-template-file "$BUILD/chat_template.jinja" \
  "$BASE" "$OUT.tmp" >"$BUILD/new_metadata.log" 2>&1
mv "$OUT.tmp" "$OUT"

# Gate: every tensor must be byte-identical to the base.
"$GGUF_PY" - "$BASE" "$OUT" <<'PY'
import sys, gguf
a, b = (gguf.GGUFReader(p) for p in sys.argv[1:])
if len(a.tensors) != len(b.tensors):
    sys.exit("FATAL: tensor count changed")
for x, y in zip(a.tensors, b.tensors):
    if x.name != y.name or x.tensor_type != y.tensor_type or x.data.tobytes() != y.data.tobytes():
        sys.exit(f"FATAL: tensor {x.name} differs from base")
name = b.fields["general.name"]
assert bytes(name.parts[name.data[0]]).decode() == "ClarkeYoursaTee"
print(f"[build] {len(b.tensors)} tensors byte-identical to base; general.name=ClarkeYoursaTee")
PY

"$GGUF_PY" "$HERE/ledger_integration/seal_model_hash.py" "$OUT" \
  --base "$BASE" --template "$BUILD/chat_template.jinja" \
  --system-prompt "$HERE/system_prompt.txt" --fewshot "$HERE/fewshot.json" --manifest "$HERE/MANIFEST.json"
