"""Which model server answers `/llm`: DeepInfer (default), ClarkeYoursaTee, Qwen GGUF or abliterated Qwen GGUF.

LLM_BACKEND=deepinfer|gguf|gguf-abliterated|clarkeyoursatee (default deepinfer)
  deepinfer         DEEPINFER_URL, default http://127.0.0.1:8090/v1/chat/completions
  gguf              LLM_URL, default http://127.0.0.1:8081/v1/chat/completions
                    (llama.cpp llama-server; Qwen2.5-1.5B-Instruct is the recommended GGUF)
  clarkeyoursatee   LLM_CLARKEYOURSATEE_URL, default http://127.0.0.1:8082/v1/chat/completions
                    (llama-server running ClarkeYoursaTee-1.5B-Q4_K_M.gguf, built by forlorn/:
                    a metadata-only derivative of Qwen2.5-1.5B-Instruct-abliterated with
                    general.name=ClarkeYoursaTee and a baked-in default system prompt;
                    weights unchanged)
  gguf-abliterated  LLM_ABLITERATED_URL, default http://127.0.0.1:8083/v1/chat/completions
                    (llama-server running Qwen2.5-1.5B-Instruct-abliterated Q4_K_M; "abliterated"
                    means its safety-refusal behaviour was removed; manual override or fallback)
LLM_FALLBACK=gguf|gguf-abliterated|clarkeyoursatee (unset = no fallback)
  Only when this is set does an unreachable DeepInfer hand the turn to another
  server. Provenance is always labeled, never shown as DeepInfer:
    gguf fallback       backend "qwen", reply lines prefixed ``[Fallback: Qwen]``
    gguf-abliterated    backend "qwen-abliterated", reply lines prefixed
                        ``[Fallback: Qwen2.5-1.5B abliterated]`` (direct or fallback)
    clarkeyoursatee     backend "clarkeyoursatee", reply lines prefixed
                        ``[ClarkeYoursaTee (Qwen2.5-1.5B-Instruct-abliterated derivative)]``
                        (direct or fallback)

The old ``deepseek-fixture`` tier was removed
with no alias: setting it is a BackendConfigError and cli_loopback exits.

Fast fail: DeepInfer liveness is a socket connect (DEEPINFER_CONNECT_TIMEOUT,
default 0.5 s) and then GET /health or /v1/models; the result is probed at
startup and cached for DEEPINFER_REPROBE_S (default 30 s), so a dead port never
holds a /llm turn.

Every URL must be loopback (Cosmic Alignment); cli_loopback refuses to start
otherwise.

ASSUMPTION (verify once a DeepInfer server exists): this repo vendors only
DeepInfer's model code (``deepinfer/model_executor/models/v4_modules``) and a
copy of its engine files (``engine/deepinfer_shim``); it has no DeepInfer server
and no API description. The bridge therefore talks to DeepInfer with the same
OpenAI-compatible request it sends llama-server (POST /v1/chat/completions with
role messages, ``choices[0].message.content`` back) and checks liveness with
GET /health, then GET /v1/models. Neither path is confirmed by the repo.

The capability probe only reports what this machine has (find_spec for
deep_gemm / deep_ep / flash_mla / torch / deepinfer._C, and
torch.cuda.is_available() when torch is installed). The bridge itself needs none
of them: it is an HTTP client.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Final, Optional, Tuple
from urllib.parse import urlsplit

logger = logging.getLogger("sovereign-irc-bridge.llm")

BACKENDS: Final = ("deepinfer", "gguf", "gguf-abliterated", "clarkeyoursatee")
FALLBACKS: Final = ("", "gguf", "gguf-abliterated", "clarkeyoursatee")
DEFAULT_BACKEND: Final = "deepinfer"
DEFAULT_DEEPINFER_URL: Final = "http://127.0.0.1:8090/v1/chat/completions"
DEFAULT_DEEPINFER_MODEL: Final = "deepinfer"
DEFAULT_CLARKEYOURSATEE_URL: Final = "http://127.0.0.1:8082/v1/chat/completions"
DEFAULT_CLARKEYOURSATEE_MODEL: Final = "clarkeyoursatee"
DEFAULT_ABLITERATED_URL: Final = "http://127.0.0.1:8083/v1/chat/completions"
DEFAULT_ABLITERATED_MODEL: Final = "qwen2.5-1.5b-instruct-abliterated"
# Values that used to be accepted and were removed with no alias; named in the error.
REMOVED_BACKENDS: Final = {"deepseek-fixture": "removed with no alias; use clarkeyoursatee"}
HEALTH_PATHS: Final = ("/health", "/v1/models")
DEFAULT_CONNECT_TIMEOUT_S: Final = 0.5   # DEEPINFER_CONNECT_TIMEOUT (socket connect)
DEFAULT_REPROBE_S: Final = 30.0          # DEEPINFER_REPROBE_S
# Provenance labels carried in route lines, JSON logs and meta["backend"].
LABEL_DEEPINFER: Final = "deepinfer"
LABEL_GGUF: Final = "gguf"
LABEL_FALLBACK: Final = "qwen"           # GGUF llama-server answering for an offline DeepInfer
LABEL_CLARKEYOURSATEE: Final = "clarkeyoursatee"  # ClarkeYoursaTee GGUF, direct or fallback
LABEL_ABLITERATED: Final = "qwen-abliterated"  # abliterated Qwen GGUF, direct or fallback
FALLBACK_PREFIX: Final = "[Fallback: Qwen] "
ABLITERATED_PREFIX: Final = "[Fallback: Qwen2.5-1.5B abliterated] "
CLARKEYOURSATEE_PREFIX: Final = "[ClarkeYoursaTee (Qwen2.5-1.5B-Instruct-abliterated derivative)] "
FALLBACK_LOG: Final = "DeepInfer unreachable, falling back to Qwen"
CLARKEYOURSATEE_FALLBACK_LOG: Final = "DeepInfer unreachable, falling back to ClarkeYoursaTee (Qwen2.5-1.5B-Instruct-abliterated derivative)"
ABLITERATED_FALLBACK_LOG: Final = "DeepInfer unreachable, falling back to Qwen2.5-1.5B abliterated"
# Modules the DeepInfer V4 code imports (see deepinfer/model_executor/models/v4_modules).
CAPABILITY_MODULES: Final = ("deep_gemm", "deep_ep", "flash_mla", "torch", "deepinfer._C")


class BackendConfigError(RuntimeError):
    """Unknown LLM_BACKEND / LLM_FALLBACK value."""


def _removed_hint(v: str) -> str:
    why = REMOVED_BACKENDS.get(v)
    return f" ({v} was {why})" if why else ""


def backend(raw: Optional[str] = None) -> str:
    v = (raw if raw is not None else os.environ.get("LLM_BACKEND", DEFAULT_BACKEND)).strip().lower() or DEFAULT_BACKEND
    if v not in BACKENDS:
        raise BackendConfigError(f"LLM_BACKEND must be one of {', '.join(BACKENDS)}, got {v!r}{_removed_hint(v)}")
    return v


def fallback(raw: Optional[str] = None) -> str:
    v = (raw if raw is not None else os.environ.get("LLM_FALLBACK", "")).strip().lower()
    if v not in FALLBACKS:
        raise BackendConfigError(f"LLM_FALLBACK must be unset or one of {', '.join(f for f in FALLBACKS if f)}, got {v!r}{_removed_hint(v)}")
    return v


def deepinfer_url_raw() -> str:
    return os.environ.get("DEEPINFER_URL", DEFAULT_DEEPINFER_URL)


def deepinfer_model() -> str:
    return os.environ.get("DEEPINFER_MODEL", DEFAULT_DEEPINFER_MODEL)


def clarkeyoursatee_url_raw() -> str:
    return os.environ.get("LLM_CLARKEYOURSATEE_URL", DEFAULT_CLARKEYOURSATEE_URL)


def clarkeyoursatee_model() -> str:
    return os.environ.get("LLM_CLARKEYOURSATEE_MODEL", DEFAULT_CLARKEYOURSATEE_MODEL)


def abliterated_url_raw() -> str:
    return os.environ.get("LLM_ABLITERATED_URL", DEFAULT_ABLITERATED_URL)


def abliterated_model() -> str:
    return os.environ.get("LLM_ABLITERATED_MODEL", DEFAULT_ABLITERATED_MODEL)


def reply_prefix(label: Optional[str]) -> str:
    """Visible provenance prefix for each reply line ("" for deepinfer and direct gguf)."""
    return {LABEL_FALLBACK: FALLBACK_PREFIX, LABEL_CLARKEYOURSATEE: CLARKEYOURSATEE_PREFIX,
            LABEL_ABLITERATED: ABLITERATED_PREFIX}.get(label or "", "")


def connect_timeout() -> float:
    try:
        return max(0.05, float(os.environ.get("DEEPINFER_CONNECT_TIMEOUT", DEFAULT_CONNECT_TIMEOUT_S)))
    except ValueError:
        return DEFAULT_CONNECT_TIMEOUT_S


def reprobe_interval() -> float:
    try:
        return max(0.0, float(os.environ.get("DEEPINFER_REPROBE_S", DEFAULT_REPROBE_S)))
    except ValueError:
        return DEFAULT_REPROBE_S


def hostport(url: str) -> str:
    p = urlsplit(url)
    return p.netloc or url


# ---------------------------------------------------------------- probes

def _base(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def probe_server(url: str, timeout: Optional[float] = None) -> Tuple[bool, str]:
    """GET base/health, then base/v1/models. (True, "GET /health 200") or (False, why).

    ``timeout`` defaults to DEEPINFER_CONNECT_TIMEOUT (1 s), so a dead port never
    holds a /llm turn for a long socket timeout.
    """
    timeout = connect_timeout() if timeout is None else timeout
    ok, why = tcp_connect(url, timeout)
    if not ok:
        return False, why
    base = _base(url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # loopback: no proxies
    last = ""
    for path in HEALTH_PATHS:
        try:
            with opener.open(urllib.request.Request(base + path, method="GET"), timeout=timeout) as resp:
                return True, f"GET {path} {resp.status}"
        except urllib.error.HTTPError as exc:
            last = f"GET {path} HTTP {exc.code}"
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
            last = f"no server at {hostport(url)} ({getattr(exc, 'reason', exc)})"
            break  # nothing listening: the second path cannot answer either
    return False, last or f"no server at {hostport(url)}"


# Cached liveness so a /llm turn re-probes at most every DEEPINFER_REPROBE_S.
_STATE: Dict[str, Tuple[bool, str, float]] = {}
_STATE_LOCK = threading.Lock()


def deepinfer_state(url: str, *, now: Callable[[], float] = time.monotonic,
                    probe: Optional[Callable[[str], Tuple[bool, str]]] = None,
                    force: bool = False) -> Tuple[bool, str]:
    """(online, detail) for ``url``, from cache unless older than the re-probe interval."""
    with _STATE_LOCK:
        hit = _STATE.get(url)
        t = now()
        if hit is not None and not force and t - hit[2] < reprobe_interval():
            return hit[0], hit[1]
        ok, detail = (probe or probe_server)(url)
        _STATE[url] = (ok, detail, t)
        return ok, detail


def mark_offline(url: str, detail: str, *, now: Callable[[], float] = time.monotonic) -> None:
    """A chat POST failed: treat DeepInfer as offline until the next re-probe."""
    with _STATE_LOCK:
        _STATE[url] = (False, detail, now())


def reset_state() -> None:
    with _STATE_LOCK:
        _STATE.clear()


def tcp_connect(url: str, timeout: Optional[float] = None) -> Tuple[bool, str]:
    """Socket-level quick connect (connect_ex) before any HTTP; bounded by ``timeout``."""
    timeout = connect_timeout() if timeout is None else timeout
    p = urlsplit(url)
    host = p.hostname or "127.0.0.1"
    port = p.port or (443 if p.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        return False, f"no server at {hostport(url)} ({exc})"
    family, stype, proto, _, addr = infos[0]
    with socket.socket(family, stype, proto) as sock:
        sock.settimeout(timeout)
        try:
            rc = sock.connect_ex(addr)
        except OSError as exc:  # timeout on some platforms raises instead of returning
            return False, f"no server at {hostport(url)} ({exc})"
    if rc != 0:
        return False, f"no server at {hostport(url)} ({os.strerror(rc) if rc > 0 else rc})"
    return True, "tcp connect ok"


def _spec_present(name: str, find_spec: Callable[[str], Any]) -> bool:
    try:
        return find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False  # e.g. parent package missing for "deepinfer._C"


def _torch_cuda() -> bool:
    try:
        import torch  # type: ignore[import-not-found]

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001 — a broken torch install just means "no CUDA"
        return False


def capabilities(find_spec: Callable[[str], Any] = importlib.util.find_spec,
                 cuda_check: Callable[[], bool] = _torch_cuda) -> Dict[str, bool]:
    caps = {name: _spec_present(name, find_spec) for name in CAPABILITY_MODULES}
    caps["cuda"] = bool(caps["torch"] and cuda_check())
    return caps


def capability_summary(caps: Dict[str, bool]) -> str:
    parts = [f"{m} {'present' if caps.get(m) else 'missing'}" for m in CAPABILITY_MODULES]
    parts.append("CUDA available" if caps.get("cuda") else "no CUDA")
    return "; ".join(parts)


def status_line(name: str, url: str, server: Tuple[bool, str], caps: Optional[Dict[str, bool]] = None) -> str:
    ok, detail = server
    if name == "gguf":
        state = "online" if ok else "OFFLINE"
        return f"[System] llm backend: gguf {state} (llama-server at {hostport(url)}; {detail})"
    if name == LABEL_ABLITERATED:
        state = "online" if ok else "OFFLINE"
        return (f"[System] llm backend: gguf-abliterated {state} (Qwen2.5-1.5B-Instruct-abliterated, "
                f"safety refusals removed; llama-server at {hostport(url)}; {detail})")
    if name == LABEL_CLARKEYOURSATEE:
        state = "online" if ok else "OFFLINE"
        return (f"[System] llm backend: clarkeyoursatee {state} (ClarkeYoursaTee, "
                f"Qwen2.5-1.5B-Instruct-abliterated derivative; llama-server at {hostport(url)}; {detail})")
    caps = caps if caps is not None else capabilities()
    state = "ONLINE" if ok else "OFFLINE"
    where = f"server at {hostport(url)}: {detail}" if ok else detail
    return f"[System] llm backend: deepinfer {state} ({where}; {capability_summary(caps)})"


def startup_probe(llm_url: str) -> str:
    """Probe the active backend once at startup, fill the cache, log one status line. Never raises."""
    try:
        b, f = backend(), fallback()
        if b == "gguf":
            line = status_line("gguf", llm_url, probe_server(llm_url, timeout=3.0))
        elif b == "gguf-abliterated":
            u = abliterated_url_raw()
            line = status_line(LABEL_ABLITERATED, u, probe_server(u, timeout=3.0))
        elif b == "clarkeyoursatee":
            u = clarkeyoursatee_url_raw()
            line = status_line(LABEL_CLARKEYOURSATEE, u, probe_server(u, timeout=3.0))
        else:
            url = deepinfer_url_raw()
            ok, detail = deepinfer_state(url, force=True)
            line = status_line("deepinfer", url, (ok, detail))
            if not ok:
                if f == "gguf":
                    line += f" → fallback gguf (Qwen at {hostport(llm_url)})"
                    logger.warning("%s (%s)", FALLBACK_LOG, detail)
                elif f == "gguf-abliterated":
                    line += f" → fallback gguf-abliterated (Qwen2.5-1.5B abliterated at {hostport(abliterated_url_raw())})"
                    logger.warning("%s (%s)", ABLITERATED_FALLBACK_LOG, detail)
                elif f == "clarkeyoursatee":
                    line += (f" → fallback clarkeyoursatee (ClarkeYoursaTee, Qwen2.5-1.5B-Instruct-abliterated "
                             f"derivative at {hostport(clarkeyoursatee_url_raw())})")
                    logger.warning("%s (%s)", CLARKEYOURSATEE_FALLBACK_LOG, detail)
                else:
                    line += " → no fallback (LLM_FALLBACK unset)"
    except Exception as exc:  # noqa: BLE001 — a probe must never stop the bridge
        line = f"[System] llm backend: probe failed ({exc})"
    logger.info("%s", line)  # cli_loopback prints it; info keeps it from showing twice
    return line


def health_blob() -> Dict[str, Any]:
    """Config plus cached liveness (no network) for the bridge's /health."""
    try:
        b, f = backend(), fallback()
    except BackendConfigError as exc:
        return {"error": str(exc)}
    url = deepinfer_url_raw()
    hit = _STATE.get(url)
    return {"backend": b, "fallback": f or None, "deepinfer_url": url,
            "clarkeyoursatee_url": clarkeyoursatee_url_raw(),
            "abliterated_url": abliterated_url_raw(),
            "deepinfer_online": None if hit is None else hit[0],
            "deepinfer_detail": None if hit is None else hit[1]}


if __name__ == "__main__":  # python -m src.llm_backend
    url = deepinfer_url_raw()
    print(status_line("deepinfer", url, probe_server(url)))
    print(json.dumps(capabilities()))
