"""Prompt routing for the `/llm` bridge: server-side chat template vs prebuilt ChatML.

Default route is ``/v1/chat/completions`` with role messages: llama-server
renders them with the GGUF's own chat template. A prebuilt ChatML prompt sent
to raw ``/completion`` is used only when

* ``LLM_PROMPT_MODE=auto`` (default) and ``GET /props`` shows no usable
  ``chat_template`` (empty, or the probe failed), or
* ``LLM_PROMPT_MODE=prebuild`` (forced, for A/B against ``chat``).

Prebuild is disabled when ``POST /tokenize`` does not turn ``<|im_start|>`` /
``<|im_end|>`` into single special-token ids (the model would see them as
plain text). That is logged loudly once; the chat route keeps working and the
bridge never crashes over it.

Both routes share one stop set per template family (``STOP_BY_FAMILY``) merged
with the role-echo stops, and the same repeat penalties. Replies are checked by
``looks_degenerate`` / ``truncate_degenerate``; the bridge keeps no chat
history, so degenerate text is never fed back into a later prompt.

Everything stays on loopback: the base URL is derived from ``LLM_URL`` and
must be 127.0.0.1 / localhost / ::1.

CLI: ``python -m src.chatml_prebuild [base]`` prints the template family, the
tokenization check and a rendered ChatML sample.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Final, List, Optional, Sequence, Tuple
from urllib.parse import urlsplit

logger = logging.getLogger("sovereign-irc-bridge.llm")

DEFAULT_BASE: Final = "http://127.0.0.1:8081"
LOOPBACK_HOSTS: Final = frozenset({"127.0.0.1", "localhost", "::1"})
CHAT_PATH: Final = "/v1/chat/completions"
COMPLETION_PATH: Final = "/completion"
MODES: Final = ("auto", "chat", "prebuild")

DEFAULT_SYSTEM: Final = "You are a helpful assistant."
REPEAT_PENALTY: Final = 1.1
REPEAT_LAST_N: Final = 256
FREQUENCY_PENALTY: Final = 0.3
NGRAM: Final = 3
MAX_NGRAM_REPEATS: Final = 4  # a word 3-gram seen more often than this is a loop

STOP_BY_FAMILY: Final[Dict[str, Tuple[str, ...]]] = {
    "chatml": ("<|im_end|>", "<|im_start|>", "<|endoftext|>", "\nUser:", "\nuser:", "\nHuman:"),
    "llama3": ("<|eot_id|>", "<|start_header_id|>", "<|end_of_text|>", "\nUser:", "\nuser:", "\nHuman:"),
    "gemma": ("<end_of_turn>", "<start_of_turn>", "<eos>", "\nUser:", "\nuser:", "\nHuman:"),
    # DeepSeek-V3/V4 templates (fullwidth bars, U+2581 in end▁of▁sentence).
    "deepseek": ("<｜end▁of▁sentence｜>", "<｜User｜>", "<｜Assistant｜>", "\nUser:", "\nuser:", "\nHuman:"),
    "unknown": ("<|im_end|>", "<|im_start|>", "<|eot_id|>", "<end_of_turn>", "<｜end▁of▁sentence｜>", "<｜User｜>", "\nUser:", "\nuser:", "\nHuman:"),
    "none": ("<|im_end|>", "<|im_start|>", "<|endoftext|>", "\nUser:", "\nuser:", "\nHuman:"),
}
# Small models that drift into writing a chat log ("User 1: … User 38: …").
ROLE_ECHO_STOPS: Final = ("User 1:", "\nUser 1:", "\nUSER:", "\nAssistant:")


class PromptConfigError(RuntimeError):
    """Base URL is not loopback, or the prompt mode is unknown."""


# ---------------------------------------------------------------- URLs / mode

def base_url(llm_url: str) -> str:
    """scheme://host:port of LLM_URL; refuses anything that is not loopback."""
    parts = urlsplit(llm_url or DEFAULT_BASE)
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or host not in LOOPBACK_HOSTS:
        raise PromptConfigError(f"LLM base must be http(s) on 127.0.0.1/localhost/::1, got {llm_url!r}")
    return f"{parts.scheme}://{parts.netloc}"


def prompt_mode(raw: Optional[str] = None) -> str:
    mode = (raw if raw is not None else os.environ.get("LLM_PROMPT_MODE", "auto")).strip().lower() or "auto"
    if mode not in MODES:
        raise PromptConfigError(f"LLM_PROMPT_MODE must be one of {', '.join(MODES)}, got {mode!r}")
    return mode


# ---------------------------------------------------------------- rendering

def render_chatml(messages: Sequence[Dict[str, str]], add_generation_prompt: bool = True,
                  default_system: str = DEFAULT_SYSTEM) -> str:
    """ChatML exactly as Qwen-style templates render it (system first, default if none)."""
    msgs = list(messages)
    if not msgs or msgs[0].get("role") != "system":
        msgs.insert(0, {"role": "system", "content": default_system})
    out = [f"<|im_start|>{m.get('role', 'user')}\n{m.get('content', '')}<|im_end|>\n" for m in msgs]
    if add_generation_prompt:
        out.append("<|im_start|>assistant\n")
    return "".join(out)


def template_family(tpl: Optional[str]) -> str:
    if tpl is None or not str(tpl).strip():
        return "none"
    t = str(tpl)
    if "<|im_start|>" in t:
        return "chatml"
    if "<|start_header_id|>" in t or "<|eot_id|>" in t:
        return "llama3"
    if "<start_of_turn>" in t:
        return "gemma"
    if "<｜User｜>" in t or "<｜Assistant｜>" in t:
        return "deepseek"
    return "unknown"


def stops_for(family: str) -> List[str]:
    out: List[str] = []
    for s in STOP_BY_FAMILY.get(family, STOP_BY_FAMILY["unknown"]) + ROLE_ECHO_STOPS:
        if s not in out:
            out.append(s)
    return out


# ---------------------------------------------------------------- server probes

def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))  # loopback: no proxies


def _get_json(url: str, timeout: float) -> Any:
    with _opener().open(urllib.request.Request(url, method="GET"), timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: Dict[str, Any], timeout: float) -> Any:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with _opener().open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def probe_props(base: str, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """GET {base}/props → dict, or None if the probe fails."""
    try:
        data = _get_json(base_url(base) + "/props", timeout)
    except (urllib.error.URLError, OSError, ValueError, PromptConfigError) as exc:
        logger.info("llm props probe failed at %s: %s", base, exc)
        return None
    return data if isinstance(data, dict) else None


def tokenize(base: str, text: str, timeout: float = 3.0) -> Optional[List[int]]:
    try:
        data = _post_json(base_url(base) + "/tokenize",
                          {"content": text, "add_special": False, "parse_special": True}, timeout)
    except (urllib.error.URLError, OSError, ValueError, PromptConfigError):
        return None
    toks = data.get("tokens") if isinstance(data, dict) else None
    if not isinstance(toks, list):
        return None
    return [t["id"] if isinstance(t, dict) else t for t in toks]


def verify_prebuild_tokenization(base: str) -> Tuple[bool, str]:
    """ChatML markers must each be one token id, or prebuild would send them as plain text."""
    ids: Dict[str, Any] = {}
    for marker in ("<|im_start|>", "<|im_end|>"):
        toks = tokenize(base, marker)
        if toks is None:
            return False, f"POST /tokenize failed for {marker}"
        if len(toks) != 1:
            return False, f"{marker} -> {len(toks)} tokens {toks[:8]} (not a single special id)"
        ids[marker] = toks[0]
    return True, "single ids " + " ".join(f"{k}={v}" for k, v in ids.items())


_PREBUILD_CHECK: Dict[str, Tuple[bool, str]] = {}


def prebuild_available(base: str) -> Tuple[bool, str]:
    """Cached per base; the first failure is logged loudly and prebuild stays off."""
    b = base_url(base)
    if b not in _PREBUILD_CHECK:
        ok, detail = verify_prebuild_tokenization(b)
        _PREBUILD_CHECK[b] = (ok, detail)
        if ok:
            logger.info("ChatML prebuild available at %s: %s", b, detail)
        else:
            logger.error("!!! ChatML prebuild DISABLED at %s: %s — /v1/chat/completions still works", b, detail)
    return _PREBUILD_CHECK[b]


def startup_check(llm_url: str) -> None:
    """Called once when the bridge starts. Never raises."""
    try:
        b = base_url(llm_url)
        props = probe_props(b)
        fam = template_family(props.get("chat_template") if props else None)
        logger.info("llm template family at %s: %s (mode=%s)", b, fam, prompt_mode())
        prebuild_available(b)
    except Exception as exc:  # noqa: BLE001 — a probe must never stop the bridge
        logger.error("llm startup check failed: %s", exc)


# ---------------------------------------------------------------- request / reply

def build_request(messages: Sequence[Dict[str, str]], base: str, mode: str = "auto", *,
                  model: str = "local-gguf", max_tokens: int = 256, temperature: float = 0.4,
                  chat_url: Optional[str] = None,
                  props: Optional[Dict[str, Any]] = None, probe: bool = True,
                  prebuild_ok: Optional[Tuple[bool, str]] = None) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """→ (url path, payload, meta). meta['path'] is the route actually taken."""
    b = base_url(base)
    mode = prompt_mode(mode)
    if props is None and probe:
        props = probe_props(b)
    family = template_family(props.get("chat_template") if props else None)
    meta: Dict[str, Any] = {"mode": mode, "family": family, "props": props is not None}
    want_prebuild = mode == "prebuild" or (mode == "auto" and family == "none")
    if want_prebuild:
        ok, detail = prebuild_ok if prebuild_ok is not None else prebuild_available(b)
        if ok:
            meta.update(path=COMPLETION_PATH, reason="forced" if mode == "prebuild" else "no chat_template")
            payload = {
                "prompt": render_chatml(messages),
                "n_predict": max_tokens,
                "temperature": temperature,
                "stop": stops_for("chatml"),
                "repeat_penalty": REPEAT_PENALTY,
                "repeat_last_n": REPEAT_LAST_N,
                "frequency_penalty": FREQUENCY_PENALTY,
                "stream": False,
            }
            meta["family_stops"] = "chatml"
            return COMPLETION_PATH, payload, meta
        meta["prebuild_disabled"] = detail
    if mode == "chat":
        reason = "forced chat"
    elif want_prebuild:
        reason = "prebuild unavailable"
    else:
        reason = "server template"
    meta.update(path=CHAT_PATH, reason=reason)
    meta["family_stops"] = family
    path = urlsplit(chat_url).path if chat_url else CHAT_PATH
    payload = {
        "model": model,
        "messages": list(messages),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        "stop": stops_for(family),
        "repeat_penalty": REPEAT_PENALTY,  # llama-server sampling option
        "repeat_last_n": REPEAT_LAST_N,
        "frequency_penalty": FREQUENCY_PENALTY,  # OpenAI-compatible field
    }
    meta["path"] = path or CHAT_PATH
    return meta["path"], payload, meta


def extract_text(data: Any) -> Optional[str]:
    """.choices[0].message.content (chat) or .content (/completion); None if neither."""
    if not isinstance(data, dict):
        return None
    try:
        return str(data["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError):
        pass
    if "content" in data:
        return str(data.get("content") or "")
    return None


def finish_reason(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    try:
        return data["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        pass
    if data.get("stopped_eos"):
        return "stop"
    if data.get("stopped_word"):
        return "stop:" + str(data.get("stopping_word", ""))
    if data.get("stopped_limit"):
        return "length"
    return data.get("stop_type")


def _ngram_starts(text: str, n: int = NGRAM) -> Dict[Tuple[str, ...], List[int]]:
    words = [(m.start(), re.sub(r"[^\w']+", "", m.group(0).lower())) for m in re.finditer(r"\S+", text)]
    words = [(pos, w) for pos, w in words if w]
    seen: Dict[Tuple[str, ...], List[int]] = {}
    for i in range(len(words) - n + 1):
        seen.setdefault(tuple(w for _, w in words[i:i + n]), []).append(words[i][0])
    return seen


def looks_degenerate(text: str, limit: int = MAX_NGRAM_REPEATS) -> bool:
    """True if any word 3-gram occurs more than ``limit`` times."""
    return any(len(p) > limit for p in _ngram_starts(text or "").values())


def truncate_degenerate(text: str, limit: int = MAX_NGRAM_REPEATS) -> Tuple[str, bool]:
    """Cut at the first repeat of the looping 3-gram; the first copy stays."""
    loops = [p for p in _ngram_starts(text or "").values() if len(p) > limit]
    if not loops:
        return text, False
    return text[: min(p[1] for p in loops)], True


# ---------------------------------------------------------------- CLI

def main(argv: Sequence[str]) -> int:
    base = argv[0] if argv else os.environ.get("LLM_URL", DEFAULT_BASE)
    try:
        b = base_url(base)
    except PromptConfigError as exc:
        print(f"FATAL: Cosmic Alignment — {exc}", file=sys.stderr)
        return 1
    props = probe_props(b)
    tpl = props.get("chat_template") if props else None
    print(f"base: {b}")
    print(f"props: {'ok' if props is not None else 'probe failed'}"
          f" model={props.get('model_path') if props else None}")
    print(f"family: {template_family(tpl)}")
    ok, detail = verify_prebuild_tokenization(b)
    print(f"prebuild tokenization: {'OK' if ok else 'DISABLED'} ({detail})")
    print(f"mode (LLM_PROMPT_MODE): {prompt_mode()}")
    sample = [{"role": "system", "content": "You describe a fruit-fly brain simulation."},
              {"role": "user", "content": "spikes[antennal lobe=4 mushroom body=3 lateral horn=5 lobula=7] total=76"}]
    print("rendered ChatML:")
    print(render_chatml(sample), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
