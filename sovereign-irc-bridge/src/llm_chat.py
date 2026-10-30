# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""`/llm` chat path for the TeaVM CLI bridge — DeepInfer or GGUF, loopback only.

Backend selection (see :mod:`src.llm_backend`): LLM_BACKEND=deepinfer (default)
posts to DEEPINFER_URL; LLM_BACKEND=gguf posts to LLM_URL (llama.cpp). With
LLM_FALLBACK=gguf an offline DeepInfer hands the turn to the GGUF server and
the reply is labeled ``backend=qwen`` / ``[Fallback: Qwen]``; with
LLM_FALLBACK=gguf-abliterated (or LLM_BACKEND=gguf-abliterated) it goes to
LLM_ABLITERATED_URL and is labeled ``backend=qwen-abliterated`` /
``[Fallback: Qwen2.5-1.5B abliterated]``; with LLM_FALLBACK=clarkeyoursatee (or
LLM_BACKEND=clarkeyoursatee) it goes to LLM_CLARKEYOURSATEE_URL and is labeled
``backend=clarkeyoursatee`` /
``[ClarkeYoursaTee (Qwen2.5-1.5B-Instruct-abliterated derivative)]``. Without a fallback the
turn ends with ``[System] llm: deepinfer backend offline (…)``.

The TeaVM chatbox sends one WebSocket frame::

    /llm <prompt>
    #neuro {...NeuronSnapshot JSON: per-lane LIF-RK4 spike counts / rates...}
    #feedback {...TracebackFeedback JSON: recent CLI traceback reports...}

This module turns that into an OpenAI-style chat request for llama.cpp's
``llama-server`` (``/v1/chat/completions``) on 127.0.0.1 and returns chat
lines. It always sends role messages (system + user), never a hand-built
``<|im_start|>`` prompt: llama-server renders them with the GGUF's own chat
template (jinja, on by default; ``--jinja`` makes it explicit). The reply goes
through ``clean_reply`` (stop sequences, role-echo cut, 3-gram loop cut). The feedback signal is traceback reports (plus local surefire test
failures when present) — never a dopamine / reward variable.

Env:
  LLM_URL        default http://127.0.0.1:8081/v1/chat/completions (loopback only)
  LLM_MODEL      default "local-gguf" (llama-server serves whatever -m loaded)
  LLM_TIMEOUT_S  default 60
  LLM_MAX_TOKENS default 256
  LLM_BUILD_FEEDBACK  "0" disables reading surefire reports into feedback
  LLM_RAW_REPLY  default "1": send the full model text (incl. reasoning) with no
                 line-cap, role-echo cut, or n-gram trim. "0" restores the guard.
  LLM_HISTORY_PATH  default /workspace/bridge-serving/llm_history.jsonl
                 (JSONL of user/assistant turns keyed by session; reloaded
                 every request so a keepalive restart still has context).
                 Empty string disables. Rows carry a ``session`` field; legacy
                 rows without it count as ``default``.
  LLM_HISTORY_MAX_TOKENS  default 2500 (chars/4 estimate); newest turns kept.
  LLM_SYSTEM_PROMPT  "spike" forces the TeaVM neuron/traceback system prompt;
                 otherwise that prompt only applies when a #neuro snapshot or
                 traceback feedback is attached. Plain /llm questions get a
                 direct assistant prompt.

If the model server is down the caller gets ``[System] llm offline: …``,
never an exception.
"""
from __future__ import annotations

import asyncio
import threading
import logging
import json
import os
import re
from datetime import datetime, timezone
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple
from urllib.parse import urlsplit

from src import chatml_prebuild, llm_backend

logger = logging.getLogger("sovereign-irc-bridge.llm")

DEFAULT_LLM_URL: Final = "http://127.0.0.1:8081/v1/chat/completions"
DEFAULT_LLM_MODEL: Final = "local-gguf"
LOOPBACK_HOSTS: Final = frozenset({"127.0.0.1", "localhost", "::1"})

NEURO_TAG: Final = "#neuro "
FEEDBACK_TAG: Final = "#feedback "
MAX_PROMPT: Final = 2000
MAX_NEURO_JSON: Final = 2000
MAX_FEEDBACK_JSON: Final = 1500
MAX_REPORTS: Final = 5
MAX_FRAMES: Final = 3
MAX_MESSAGE: Final = 200
MAX_REPLY_LINES: Final = 40
DEFAULT_HISTORY_PATH: Final = "/workspace/bridge-serving/llm_history.jsonl"
DEFAULT_HISTORY_MAX_TOKENS: Final = 2500
DEFAULT_SESSION: Final = "default"
SESSION_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_HISTORY_LOCK: Final = threading.Lock()
PLAIN_SYSTEM_PROMPT: Final = (
    "You are a helpful assistant. Answer the user's question directly and clearly. "
    "Do not invent neuron snapshots, spike counts, or traceback reports unless the "
    "user message actually includes them."
)

# Reply guard. Small GGUF models sometimes stop answering and start writing the
# rest of a chat log ("User 1: … User 38: …") or loop on one sentence. The model
# server is asked to stop there (per-template-family stop set + role-echo stops
# and repeat penalties, see chatml_prebuild), and clean_reply() trims whatever
# still gets through.
STOP_SEQUENCES: Final = tuple(chatml_prebuild.stops_for("chatml"))
MAX_NGRAM_REPEATS: Final = chatml_prebuild.MAX_NGRAM_REPEATS
ROLE_ECHO_RE: Final = re.compile(r"(?im)^[ \t>*_-]*(user|assistant|system)\s*\d*\s*:")
# DeepSeek-V3/V4 turn markers in the text = the model wrote another turn.
DEEPSEEK_TURN_RE: Final = re.compile(r"<｜(?:User|Assistant|end▁of▁sentence)｜>")
THINK_TAG_RE: Final = re.compile(r"</?think>")

_REPO_ROOT = Path(__file__).resolve().parents[2]
SUREFIRE_DIR: Final = _REPO_ROOT / "games" / "teavm-rhythm" / "target" / "surefire-reports"

SYSTEM_PROMPT: Final = (
    "You are the chat voice of a TeaVM rhythm game played by a simulated fruit-fly brain "
    "(leaky integrate-and-fire neurons, RK4, 1 ms substeps; one motor neuron per lane, a spike "
    "is a key press). Each user turn carries NEURON_SNAPSHOT (real spike counts/rates over the "
    "last window_ms, ending at window_end_ms; window_anchor last_spike means the song's cues are "
    "done and the window shows its final spikes; per-lane total = all spikes this song; "
    "membrane voltages in mV, most recently active neurons) and FEEDBACK "
    "(recent traceback reports from the chat's Python tool calls and failing tests). "
    "FEEDBACK is your training signal: if it holds errors, explain the likely cause and "
    "suggest a concrete fix first. Only describe neuron activity that the snapshot shows; "
    "if brain is idle say so. Be brief (under 120 words)."
)




def raw_reply_enabled() -> bool:
    """LLM_RAW_REPLY defaults on: show the full model text, including garbled bits."""
    return os.environ.get("LLM_RAW_REPLY", "1").strip().lower() not in ("0", "false", "no", "off")


def history_path() -> Optional[Path]:
    raw = os.environ.get("LLM_HISTORY_PATH", DEFAULT_HISTORY_PATH)
    if raw is None or str(raw).strip() == "":
        return None
    return Path(str(raw).strip())


def history_max_tokens() -> int:
    try:
        return max(0, int(os.environ.get("LLM_HISTORY_MAX_TOKENS", DEFAULT_HISTORY_MAX_TOKENS)))
    except ValueError:
        return DEFAULT_HISTORY_MAX_TOKENS


def _est_tokens(text: str) -> int:
    return max(1, (len(text or "") + 3) // 4)


def normalize_session(raw: Optional[str]) -> str:
    """Validate ``?session=`` → ``[A-Za-z0-9_-]{1,64}``, else ``default``."""
    s = (raw or "").strip()
    if s and SESSION_RE.fullmatch(s):
        return s
    return DEFAULT_SESSION


def _row_session(row: Dict[str, Any]) -> str:
    """Legacy rows without a session field count as ``default``."""
    s = row.get("session")
    if isinstance(s, str) and SESSION_RE.fullmatch(s.strip()):
        return s.strip()
    return DEFAULT_SESSION


def _read_all_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    except OSError as exc:
        logger.warning("llm history read failed (%s): %s", path, exc)
    return rows


def _atomic_rewrite(path: Path, rows: List[Dict[str, Any]]) -> None:
    """Write JSONL via ``.tmp`` + ``os.replace`` (crash-safe). Caller holds the lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load_history(path: Optional[Path] = None, session: str = DEFAULT_SESSION) -> List[Dict[str, str]]:
    """Read JSONL turns for ``session`` (legacy rows → default). Missing file → []."""
    path = history_path() if path is None else path
    session = normalize_session(session)
    if path is None or not path.is_file():
        return []
    turns: List[Dict[str, str]] = []
    with _HISTORY_LOCK:
        rows = _read_all_rows(path)
    for row in rows:
        if _row_session(row) != session:
            continue
        role, content = row.get("role"), row.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            turns.append({"role": role, "content": content})
    return turns


def trim_history(turns: List[Dict[str, str]], budget: Optional[int] = None) -> List[Dict[str, str]]:
    """Keep the newest turns that fit ``budget`` tokens (chars/4). Prefer whole pairs."""
    budget = history_max_tokens() if budget is None else budget
    if budget <= 0 or not turns:
        return []
    kept: List[Dict[str, str]] = []
    used = 0
    for turn in reversed(turns):
        cost = _est_tokens(turn["content"])
        if kept and used + cost > budget:
            break
        if not kept and cost > budget:
            # single oversized turn: still keep a tail so the model has something
            kept.append({"role": turn["role"], "content": turn["content"][-(budget * 4):]})
            break
        kept.append(turn)
        used += cost
    kept.reverse()
    # Drop a leading orphan assistant so the first history role is user when possible
    if kept and kept[0]["role"] == "assistant":
        kept = kept[1:]
    return kept


def append_history(user: str, assistant: str, path: Optional[Path] = None,
                   session: str = DEFAULT_SESSION) -> None:
    """Append one user/assistant pair as JSONL with ``session``; fsync. Never raises."""
    path = history_path() if path is None else path
    session = normalize_session(session)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with _HISTORY_LOCK:
            with path.open("a", encoding="utf-8") as fh:
                for role, content in (("user", user), ("assistant", assistant)):
                    fh.write(json.dumps(
                        {"role": role, "content": content, "session": session, "ts": ts},
                        ensure_ascii=False,
                    ) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
    except OSError as exc:
        logger.warning("llm history append failed (%s): %s", path, exc)


def archive_history(path: Optional[Path] = None, session: str = DEFAULT_SESSION) -> Optional[Path]:
    """Archive only ``session`` rows to ``*.reset-<session>-<utc>``; leave others.

    Remaining rows are rewritten atomically via ``.tmp`` + ``os.replace``.
    → archive path, or None if that session had nothing to archive.
    """
    path = history_path() if path is None else path
    session = normalize_session(session)
    if path is None:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = path.with_name(f"{path.name}.reset-{session}-{stamp}")
    try:
        with _HISTORY_LOCK:
            if not path.is_file():
                return None
            rows = _read_all_rows(path)
            keep = [r for r in rows if _row_session(r) != session]
            archived = [r for r in rows if _row_session(r) == session]
            if not archived:
                return None
            # Write archive first (atomic), then rewrite the live file.
            _atomic_rewrite(dest, archived)
            if keep:
                _atomic_rewrite(path, keep)
            else:
                # No other sessions left — remove the live file.
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                # Drop a leftover .tmp if any prior crash left one.
                tmp = path.with_name(path.name + ".tmp")
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
        return dest
    except OSError as exc:
        logger.warning("llm history archive failed (%s): %s", path, exc)
        return None



def use_spike_prompt(neuro: Optional[Dict[str, Any]], feedback: Dict[str, Any]) -> bool:
    force = os.environ.get("LLM_SYSTEM_PROMPT", "").strip().lower()
    if force in ("spike", "neuro", "traceback"):
        return True
    if force in ("plain", "direct", "none"):
        return False
    if neuro:
        return True
    reports = feedback.get("reports") if isinstance(feedback, dict) else None
    return bool(reports)


class LlmConfigError(RuntimeError):
    """LLM_URL points somewhere other than loopback."""


def is_llm_line(text: str) -> bool:
    first = (text or "").strip().split("\n", 1)[0].strip().lower()
    return first == "/llm" or first.startswith("/llm ")


def llm_url() -> str:
    return assert_loopback_url(os.environ.get("LLM_URL", DEFAULT_LLM_URL))


def llm_model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)


def assert_loopback_url(url: str, name: str = "LLM_URL") -> str:
    """The model server must be on 127.0.0.1 / localhost / ::1 (Cosmic Alignment)."""
    parts = urlsplit((url or "").strip())
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or host not in LOOPBACK_HOSTS:
        raise LlmConfigError(
            f"{name} must be http(s)://127.0.0.1|localhost|[::1]…, got {url!r}"
        )
    return url.strip()


def deepinfer_url() -> str:
    return assert_loopback_url(llm_backend.deepinfer_url_raw(), "DEEPINFER_URL")


def _trim(s: Any, n: int) -> str:
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def parse_wire(text: str) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[str]]:
    """Split a /llm frame → (prompt, neuro, feedback, notes). Bad JSON becomes a note."""
    notes: List[str] = []
    lines = (text or "").split("\n")
    head = lines[0].strip()
    prompt = head[4:].strip() if head.lower().startswith("/llm") else head
    neuro: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None
    for raw in lines[1:]:
        line = raw.strip()
        for tag, cap, name in ((NEURO_TAG, MAX_NEURO_JSON, "neuro"), (FEEDBACK_TAG, MAX_FEEDBACK_JSON * 4, "feedback")):
            if line.startswith(tag.strip()):
                blob = line[len(tag.strip()):].strip()
                if len(blob) > cap:
                    notes.append(f"{name} block too large ({len(blob)} chars) — dropped")
                    break
                try:
                    val = json.loads(blob)
                except json.JSONDecodeError as exc:
                    notes.append(f"{name} block is not JSON ({exc.msg}) — dropped")
                    break
                if not isinstance(val, dict):
                    notes.append(f"{name} block is not an object — dropped")
                    break
                if name == "neuro":
                    neuro = val
                else:
                    feedback = val
                break
    return _trim(prompt, MAX_PROMPT), neuro, feedback, notes


def _clean_report(r: Any, origin: str) -> Optional[Dict[str, Any]]:
    if not isinstance(r, dict):
        return None
    frames = r.get("frames") or []
    if not isinstance(frames, list):
        frames = []
    return {
        "type": _trim(r.get("type") or "Error", 80),
        "message": _trim(r.get("message") or "", MAX_MESSAGE),
        "origin": _trim(r.get("origin") or origin, 20),
        "frames": [_trim(f, 120) for f in frames[-MAX_FRAMES:]],
    }


_FAIL_RE = re.compile(r"^(?P<test>\S+)\s+--\s+Time elapsed.*<<<\s+(FAILURE|ERROR)!", re.M)


def collect_build_feedback(directory: Path = SUREFIRE_DIR) -> List[Dict[str, Any]]:
    """Failing JUnit tests from the last local `mvn` run (surefire *.txt), trimmed."""
    if os.environ.get("LLM_BUILD_FEEDBACK", "1") == "0" or not directory.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for p in sorted(directory.glob("*.txt")):
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _FAIL_RE.finditer(body):
            tail = body[m.end():].lstrip("\n").splitlines()
            exc_line = tail[0] if tail else ""
            etype, _, emsg = exc_line.partition(":")
            frames = [ln.strip()[3:] for ln in tail[1:] if ln.strip().startswith("at ")]
            # keep the test's own frames, newest last-few
            own = [f for f in frames if "junit" not in f and "java.base" not in f] or frames
            out.append(
                _clean_report(
                    {"type": etype.strip() or "TestFailure", "message": emsg.strip() or m.group("test"),
                     "frames": [m.group("test")] + own[:MAX_FRAMES - 1]},
                    "mvn-test",
                )
            )
    return [r for r in out if r][-MAX_REPORTS:]


def merge_feedback(cli: Optional[Dict[str, Any]], build: List[Dict[str, Any]]) -> Dict[str, Any]:
    """CLI traceback reports + build/test failures → one capped feedback block."""
    reports: List[Dict[str, Any]] = []
    dropped = 0
    if cli:
        raw = cli.get("reports") or []
        if isinstance(raw, list):
            reports.extend(r for r in (_clean_report(x, "cli") for x in raw) if r)
        try:
            dropped = int(cli.get("dropped") or 0)
        except (TypeError, ValueError):
            dropped = 0
    reports.extend(build)
    if len(reports) > MAX_REPORTS:
        dropped += len(reports) - MAX_REPORTS
        reports = reports[-MAX_REPORTS:]
    block = {"kind": "traceback", "reports": reports, "dropped": dropped}
    while len(json.dumps(block, ensure_ascii=False)) > MAX_FEEDBACK_JSON and block["reports"]:
        block["reports"].pop(0)
        block["dropped"] += 1
    return block


def build_messages(prompt: str, neuro: Optional[Dict[str, Any]], feedback: Dict[str, Any],
                   history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """System + trimmed prior turns + current user. Spike prompt only with neuro/feedback (or force)."""
    spike = use_spike_prompt(neuro, feedback)
    if spike:
        neuro_txt = json.dumps(neuro, separators=(",", ":")) if neuro else "none (client sent no snapshot)"
        fb_txt = json.dumps(feedback, separators=(",", ":"), ensure_ascii=False)
        user = (
            f"NEURON_SNAPSHOT: {neuro_txt}\n"
            f"FEEDBACK: {fb_txt}\n"
            f"USER: {prompt or '(empty — summarise the brain state and any feedback)'}"
        )
        system = SYSTEM_PROMPT
    else:
        user = prompt or "(empty)"
        system = PLAIN_SYSTEM_PROMPT
    msgs: List[Dict[str, str]] = [{"role": "system", "content": system}]
    msgs.extend(trim_history(history or []))
    msgs.append({"role": "user", "content": user})
    return msgs


def _post(url: str, payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # No proxies: the model server is on loopback.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def complete(messages: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str]]:
    """→ (reply, None) or (None, offline-reason). Never raises."""
    reply, err, _meta = complete_routed(messages)
    return reply, err


def complete_routed(messages: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Like complete(), plus route meta. meta["backend"] is the provenance label:
    "deepinfer", "gguf" (LLM_BACKEND=gguf), "qwen" (GGUF fallback for an offline
    DeepInfer), "qwen-abliterated" (abliterated Qwen GGUF, direct or fallback) or
    "clarkeyoursatee" (ClarkeYoursaTee GGUF, direct or fallback)."""
    try:
        be, fb = llm_backend.backend(), llm_backend.fallback()
    except llm_backend.BackendConfigError as exc:
        return None, str(exc), {"backend": None}
    if be == "gguf":
        return _complete_gguf(messages, llm_backend.LABEL_GGUF)
    if be == "clarkeyoursatee":
        return _complete_clarkeyoursatee(messages)
    if be == "gguf-abliterated":
        return _complete_abliterated(messages)
    try:
        url = deepinfer_url()
    except LlmConfigError as exc:
        return None, str(exc), {"backend": llm_backend.LABEL_DEEPINFER}
    online, detail = llm_backend.deepinfer_state(url)
    err: Optional[str] = None
    if online:
        reply, err, meta = _complete_at(lambda: url, llm_backend.deepinfer_model(), messages)
        meta["backend"] = llm_backend.LABEL_DEEPINFER
        if err is None:
            return reply, None, meta
        llm_backend.mark_offline(url, err)
        detail = err
    offline = f"deepinfer backend offline ({detail})"
    if fb == "gguf":
        logger.warning("%s (%s)", llm_backend.FALLBACK_LOG, detail)
        reply, err, meta = _complete_gguf(messages, llm_backend.LABEL_FALLBACK)
    elif fb == "gguf-abliterated":
        logger.warning("%s (%s)", llm_backend.ABLITERATED_FALLBACK_LOG, detail)
        reply, err, meta = _complete_abliterated(messages)
    elif fb == "clarkeyoursatee":
        logger.warning("%s (%s)", llm_backend.CLARKEYOURSATEE_FALLBACK_LOG, detail)
        reply, err, meta = _complete_clarkeyoursatee(messages)
    else:
        return None, offline, {"backend": llm_backend.LABEL_DEEPINFER, "deepinfer_offline": offline}
    meta.update(fallback_from="deepinfer", deepinfer_offline=offline)
    return reply, err, meta


def backend_order_line(meta: Dict[str, Any]) -> Optional[str]:
    """Explicit backend order for LLM_BACKEND=deepinfer (env contract unchanged).

    Primary is DeepInfer (https://github.com/deepseek-ai/DeepInfer, DEEPINFER_URL,
    default 127.0.0.1:8090). Secondary is LLM_FALLBACK; the clarkeyoursatee
    fallback is called the "deepseek tutor" only when LLM_CLARKEYOURSATEE_MODEL
    names a deepseek model (deepseek-r2-1.5b on 127.0.0.1:8085 in production),
    so the label never claims a model that is not being served.
    """
    be = meta.get("backend")
    if meta.get("fallback_from") != llm_backend.LABEL_DEEPINFER and be != llm_backend.LABEL_DEEPINFER:
        return None
    if not meta.get("fallback_from"):
        if meta.get("deepinfer_offline"):
            return "[System] llm order: primary=deepinfer offline, no secondary (LLM_FALLBACK unset)"
        return "[System] llm order: primary=deepinfer answered"
    if be == llm_backend.LABEL_CLARKEYOURSATEE:
        model = llm_backend.clarkeyoursatee_model()
        name = "deepseek tutor" if "deepseek" in model.lower() else "clarkeyoursatee"
        secondary = f"{name} ({model})"
    else:
        secondary = str(be)
    return f"[System] llm order: primary=deepinfer offline → secondary: {secondary} answered"


def _complete_gguf(messages, label: str):
    reply, err, meta = _complete_at(llm_url, llm_model(), messages)
    meta["backend"] = label
    return reply, err, meta


def _complete_abliterated(messages):
    # Same Qwen chat template family and reply guard as the plain gguf path,
    # but its own server, model name and provenance label.
    reply, err, meta = _complete_at(
        lambda: assert_loopback_url(llm_backend.abliterated_url_raw(), "LLM_ABLITERATED_URL"),
        llm_backend.abliterated_model(), messages)
    meta["backend"] = llm_backend.LABEL_ABLITERATED
    return reply, err, meta


def _complete_clarkeyoursatee(messages):
    # Qwen ChatML family (ClarkeYoursaTee is a Qwen2.5 derivative); own server,
    # model name and provenance label.
    reply, err, meta = _complete_at(
        lambda: assert_loopback_url(llm_backend.clarkeyoursatee_url_raw(), "LLM_CLARKEYOURSATEE_URL"),
        llm_backend.clarkeyoursatee_model(), messages)
    meta["backend"] = llm_backend.LABEL_CLARKEYOURSATEE
    return reply, err, meta


def _complete_at(url_fn, model: str, messages: List[Dict[str, str]],
                 extra: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """One OpenAI-style request through the chatml_prebuild routing + guard pipeline."""
    meta: Dict[str, Any] = {}
    try:
        url = url_fn()
        base = chatml_prebuild.base_url(url)
        path, payload, meta = chatml_prebuild.build_request(
            messages, base, chatml_prebuild.prompt_mode(),
            model=model,
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "256")),
            chat_url=url,
        )
    except (LlmConfigError, chatml_prebuild.PromptConfigError) as exc:
        return None, str(exc), meta
    if extra and path != chatml_prebuild.COMPLETION_PATH:
        payload.update(extra)
    target = url if path == urlsplit(url).path else base + path
    logger.info("llm route path=%s mode=%s family=%s reason=%s",
                meta.get("path"), meta.get("mode"), meta.get("family"), meta.get("reason"))
    try:
        data = _post(target, payload, float(os.environ.get("LLM_TIMEOUT_S", "60")))
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code} from {target}", meta
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return None, f"{target} unreachable ({reason})", meta
    except (ValueError, json.JSONDecodeError) as exc:
        return None, f"bad JSON from {target} ({exc})", meta
    reply = chatml_prebuild.extract_text(data)
    if reply is None:
        return None, f"unexpected response shape from {target}", meta
    meta["finish_reason"] = chatml_prebuild.finish_reason(data)
    reasoning = _extract_reasoning(data)
    if reasoning:
        meta["reasoning"] = reasoning
    return reply.strip(), None, meta


def _extract_reasoning(data: Any) -> Optional[str]:
    """OpenAI-style ``message.reasoning_content`` (DeepSeek-R1 / llama-server)."""
    if not isinstance(data, dict):
        return None
    try:
        raw = data["choices"][0]["message"].get("reasoning_content")
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _cut_role_echo(text: str) -> Tuple[str, bool]:
    hits = [m.start() for m in (ROLE_ECHO_RE.search(text), DEEPSEEK_TURN_RE.search(text)) if m]
    if not hits:
        return text, False
    return text[: min(hits)], True


def _cut_repeats(text: str, limit: int = MAX_NGRAM_REPEATS) -> Tuple[str, bool]:
    """Truncate at the first repeat of any word 3-gram that occurs more than ``limit`` times."""
    return chatml_prebuild.truncate_degenerate(text, limit)


def clean_reply(raw: str) -> Tuple[str, List[str]]:
    """→ (reply, notes). Cuts role echoes and n-gram loops; a normal reply is returned unchanged."""
    text = THINK_TAG_RE.sub("", raw or "")  # bare <think>/</think> tags, content kept
    notes: List[str] = []
    text, echoed = _cut_role_echo(text)
    if echoed:
        notes.append("reply trimmed at a role echo (model began writing other chat turns)")
    text, looped = _cut_repeats(text)
    if looped:
        notes.append(f"reply trimmed at a repeat loop (a 3-word phrase recurred more than {MAX_NGRAM_REPEATS} times)")
    return text.strip(), notes


def _neuro_line(neuro: Optional[Dict[str, Any]]) -> str:
    if not neuro:
        return "[System] llm: no neuron snapshot attached"
    lanes = neuro.get("lanes") or []
    per = " ".join(
        f"{l.get('label', l.get('lane'))}={l.get('spikes')}" for l in lanes if isinstance(l, dict)
    )
    line = (
        f"[System] llm ctx: brain={neuro.get('brain')} mode={neuro.get('mode')} "
        f"window={neuro.get('window_ms')}ms spikes[{per or '—'}]"
    )
    # Where the window ends and the song's cumulative count (= the HUD's spike counter),
    # so a quiet window after the song is never read as a silent brain.
    if "window_end_ms" in neuro:
        line += f" end={neuro.get('window_end_ms')}ms({neuro.get('window_anchor')})"
    if "total_spikes" in neuro:
        line += f" total={neuro.get('total_spikes')}"
    return line


def _format_reply_lines(reply: str, meta: Dict[str, Any], *, raw: bool) -> Tuple[List[str], List[str], str]:
    """→ (engine_lines, system_notes, plain_assistant_text_for_history).

    When ``raw`` is True the full text (and any reasoning) is shown with no
    line cap and without role-echo / n-gram cuts. Reasoning is wrapped in
    ``[thinking]`` / ``[/thinking]`` markers so the chat can keep it.
    """
    notes: List[str] = []
    reasoning = (meta.get("reasoning") or "").strip()
    text = reply or ""
    if raw:
        # Keep bare <think> tags visible; still strip nothing of substance.
        body_src = text
    else:
        if chatml_prebuild.looks_degenerate(text):
            logger.warning("llm reply degenerate (3-gram loop); truncating, never fed back as context")
        body_src, trims = clean_reply(text)
        notes.extend(trims)
        reasoning = THINK_TAG_RE.sub("", reasoning).strip() if reasoning else ""
    prefix = llm_backend.reply_prefix(meta.get("backend"))
    engine: List[str] = []
    hist_parts: List[str] = []
    if reasoning:
        engine.append(f"[Engine] llm: {prefix}[thinking]")
        hist_parts.append("[thinking]")
        for ln in reasoning.splitlines() or [reasoning]:
            engine.append(f"[Engine] llm: {prefix}{ln}" if ln.strip() else f"[Engine] llm: {prefix}")
            hist_parts.append(ln)
        engine.append(f"[Engine] llm: {prefix}[/thinking]")
        hist_parts.append("[/thinking]")
    body = [ln for ln in body_src.splitlines()] if raw else [ln for ln in body_src.splitlines() if ln.strip()]
    if not body and not reasoning:
        body = ["(empty reply)"]
    limit = None if raw else MAX_REPLY_LINES
    for ln in (body if limit is None else body[:limit]):
        engine.append(f"[Engine] llm: {prefix}{ln}" if (ln or raw) else f"[Engine] llm: {prefix}")
        hist_parts.append(ln)
    if limit is not None and len(body) > limit:
        notes.append(f"reply truncated to {MAX_REPLY_LINES} lines (set LLM_RAW_REPLY=1 for the full text)")
    plain = "\n".join(hist_parts).strip() or "(empty reply)"
    return engine, notes, plain


def handle_llm_sync(text: str, session: str = DEFAULT_SESSION) -> List[str]:
    session = normalize_session(session)
    prompt, neuro, cli_fb, notes = parse_wire(text)
    # /llm reset — archive only this session's rows; other sessions stay put.
    if prompt.strip().lower() == "reset":
        archived = archive_history(session=session)
        if archived is None:
            return [f"[System] llm: history already empty for session={session} (nothing to reset)"]
        return [f"[System] llm: session={session} history archived to {archived}"]

    feedback = merge_feedback(cli_fb, collect_build_feedback())
    lines = [f"[System] llm: {n}" for n in notes]
    lines.append(f"[System] llm session: {session}")
    spike = use_spike_prompt(neuro, feedback)
    if spike or neuro is not None:
        lines.append(_neuro_line(neuro))
        lines.append(f"[System] llm ctx: feedback={len(feedback['reports'])} traceback report(s)")
    else:
        lines.append("[System] llm ctx: plain (no neuron snapshot / traceback; spike prompt off)")

    prior = load_history(session=session)
    messages = build_messages(prompt, neuro, feedback, history=prior)
    reply, err, meta = complete_routed(messages)
    logger.info("llm_reply %s", json.dumps({
        "backend": meta.get("backend"), "fallback_from": meta.get("fallback_from"),
        "path": meta.get("path"), "ok": err is None, "raw": raw_reply_enabled(),
        "session": session, "history_turns": len(trim_history(prior)), "spike_prompt": spike}))
    if meta.get("deepinfer_offline"):
        lines.append(f"[System] llm: {meta['deepinfer_offline']}")
    order = backend_order_line(meta)
    if order is not None:
        lines.append(order)
        logger.info("llm_order %s", order.removeprefix("[System] llm order: "))
    fallback = bool(meta.get("fallback_from"))
    via = {llm_backend.LABEL_FALLBACK: "gguf fallback", llm_backend.LABEL_CLARKEYOURSATEE: "clarkeyoursatee fallback",
           llm_backend.LABEL_ABLITERATED: "gguf-abliterated fallback"}
    label = f"{meta.get('backend')}" + (
        f" ({via.get(meta.get('backend'), 'fallback')} from deepinfer)" if fallback else "")
    if meta.get("path"):
        lines.append(
            f"[System] llm route: backend={label} path={meta['path']} mode={meta.get('mode')} family={meta.get('family')}"
            + (f" (prebuild off: {meta['prebuild_disabled']})" if meta.get("prebuild_disabled") else "")
        )
    elif meta.get("backend"):
        lines.append(f"[System] llm route: backend={label} (offline)")
    if err is not None:
        if meta.get("deepinfer_offline") and not fallback:
            return lines  # the "deepinfer backend offline (…)" line is the answer
        lines.append(f"[System] llm offline: {err}")
        return lines

    engine, trims, plain = _format_reply_lines(reply or "", meta, raw=raw_reply_enabled())
    lines.extend(f"[System] llm: {n}" for n in trims)
    lines.extend(engine)
    # Persist the turn the model actually saw (plain user text, not the snapshot wrapper)
    # so cold-start reloads stay useful for ordinary chat.
    append_history(prompt or "(empty)", plain, session=session)
    return lines




async def handle_llm(text: str, session: str = DEFAULT_SESSION) -> List[str]:
    """Async wrapper so the WebSocket loop never blocks on the model."""
    return await asyncio.to_thread(handle_llm_sync, text, normalize_session(session))
