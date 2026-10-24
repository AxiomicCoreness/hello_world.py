"""`/llm` chat path for the TeaVM CLI bridge — GGUF via llama.cpp, loopback only.

The TeaVM chatbox sends one WebSocket frame::

    /llm <prompt>
    #neuro {...NeuronSnapshot JSON: per-lane LIF-RK4 spike counts / rates...}
    #feedback {...TracebackFeedback JSON: recent CLI traceback reports...}

This module turns that into an OpenAI-style chat request for llama.cpp's
``llama-server`` (``/v1/chat/completions``) on 127.0.0.1 and returns chat
lines. The feedback signal is traceback reports (plus local surefire test
failures when present) — never a dopamine / reward variable.

Env:
  LLM_URL        default http://127.0.0.1:8081/v1/chat/completions (loopback only)
  LLM_MODEL      default "local-gguf" (llama-server serves whatever -m loaded)
  LLM_TIMEOUT_S  default 60
  LLM_MAX_TOKENS default 256
  LLM_BUILD_FEEDBACK  "0" disables reading surefire reports into feedback

If the model server is down the caller gets ``[System] llm offline: …``,
never an exception.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple
from urllib.parse import urlsplit

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


class LlmConfigError(RuntimeError):
    """LLM_URL points somewhere other than loopback."""


def is_llm_line(text: str) -> bool:
    first = (text or "").strip().split("\n", 1)[0].strip().lower()
    return first == "/llm" or first.startswith("/llm ")


def llm_url() -> str:
    return assert_loopback_url(os.environ.get("LLM_URL", DEFAULT_LLM_URL))


def llm_model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)


def assert_loopback_url(url: str) -> str:
    """The model server must be on 127.0.0.1 / localhost / ::1 (Cosmic Alignment)."""
    parts = urlsplit((url or "").strip())
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or host not in LOOPBACK_HOSTS:
        raise LlmConfigError(
            f"LLM_URL must be http(s)://127.0.0.1|localhost|[::1]…, got {url!r}"
        )
    return url.strip()


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


def build_messages(prompt: str, neuro: Optional[Dict[str, Any]], feedback: Dict[str, Any]) -> List[Dict[str, str]]:
    neuro_txt = json.dumps(neuro, separators=(",", ":")) if neuro else "none (client sent no snapshot)"
    fb_txt = json.dumps(feedback, separators=(",", ":"), ensure_ascii=False)
    user = (
        f"NEURON_SNAPSHOT: {neuro_txt}\n"
        f"FEEDBACK: {fb_txt}\n"
        f"USER: {prompt or '(empty — summarise the brain state and any feedback)'}"
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


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
    try:
        url = llm_url()
    except LlmConfigError as exc:
        return None, str(exc)
    payload = {
        "model": llm_model(),
        "messages": messages,
        "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "256")),
        "temperature": 0.4,
        "stream": False,
    }
    try:
        data = _post(url, payload, float(os.environ.get("LLM_TIMEOUT_S", "60")))
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code} from {url}"
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return None, f"{url} unreachable ({reason})"
    except (ValueError, json.JSONDecodeError) as exc:
        return None, f"bad JSON from {url} ({exc})"
    try:
        reply = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None, f"unexpected response shape from {url}"
    return str(reply or "").strip(), None


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


def handle_llm_sync(text: str) -> List[str]:
    prompt, neuro, cli_fb, notes = parse_wire(text)
    feedback = merge_feedback(cli_fb, collect_build_feedback())
    lines = [f"[System] llm: {n}" for n in notes]
    lines.append(_neuro_line(neuro))
    lines.append(f"[System] llm ctx: feedback={len(feedback['reports'])} traceback report(s)")
    reply, err = complete(build_messages(prompt, neuro, feedback))
    if err is not None:
        lines.append(f"[System] llm offline: {err}")
        return lines
    body = [ln for ln in (reply or "").splitlines() if ln.strip()] or ["(empty reply)"]
    for ln in body[:MAX_REPLY_LINES]:
        lines.append(f"[Engine] llm: {ln}")
    return lines


async def handle_llm(text: str) -> List[str]:
    """Async wrapper so the WebSocket loop never blocks on the model."""
    return await asyncio.to_thread(handle_llm_sync, text)
