"""TeaVM CLI WebSocket — Cosmic Alignment loopback bind.

Binds **127.0.0.1:6680** only (never 0.0.0.0). Path {@code /cli}.

Browser contract: {@code ws://127.0.0.1:6680/cli}
Remote label behind this bridge: {@code irc.abjects.net:6669}

Default mode is local echo / Engine stubs (no outbound IRC) so CI stays
offline. Set {@code CLI_LIVE_IRC=1} to open a plain TCP dial to the remote
label (still from this process, not from the browser).

pythonIDE path: lines starting with ``/py``, ``py``, ``/ide``, or ``ide``
are routed through ``pythonIDE.toolkit.SovereignToolkit`` (and pointer_2300
for ``pointer``). Failures are sent back as ``[Traceback]`` lines so the
TeaVM chat history shows a useful Python traceback.

LLM chat: ``/llm <text>`` (+ ``#neuro`` spike snapshot and ``#feedback``
traceback block) is forwarded by :mod:`src.llm_chat` to llama.cpp's
``llama-server`` on ``LLM_URL`` (default http://127.0.0.1:8081, loopback
only). Model down → ``[System] llm offline: …``, never a crash.

Extra demos: ``/py deepinfer`` (engine.deepinfer_accelerator) and
``/py katex`` / ``/katex`` (mvn -Dtest=KaTeXMacroSetTest or python mirror).
"""
from __future__ import annotations

import ast
import asyncio
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Final, List, Optional

from src.llm_chat import (
    LlmConfigError,
    assert_loopback_url,
    handle_llm,
    is_llm_line,
)

logger = logging.getLogger("sovereign-irc-bridge.cli")

# FastAPI needs WebSocket in this module's globals when `from __future__
# import annotations` is on — local imports inside create_app() are not
# visible to get_type_hints, so the param becomes a bogus query field (403).
try:
    from fastapi import WebSocket as FastAPIWebSocket
except ModuleNotFoundError:  # optional until serve time
    FastAPIWebSocket = None  # type: ignore[assignment,misc]

LOOPBACK_HOST: Final = "127.0.0.1"
CLI_PORT: Final = 6680
REMOTE_IRC: Final = "irc.abjects.net:6669"
ALLOWED_BIND: Final = frozenset({"127.0.0.1", "::1"})

# Repo root (…/hello_world.py) so `pythonIDE` imports resolve when the bridge
# is started from sovereign-irc-bridge/.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def assert_loopback_bind(host: str) -> str:
    """Non-negotiable: CLI must not listen on 0.0.0.0 / LAN interfaces."""
    h = (host or "").strip()
    if h not in ALLOWED_BIND:
        raise RuntimeError(
            f"CLI Cosmic Alignment requires bind in {sorted(ALLOWED_BIND)}, got {host!r}"
        )
    return h


def _is_ide_line(text: str) -> bool:
    t = (text or "").strip().lower()
    return (
        t.startswith("/py")
        or t.startswith("/ide")
        or t.startswith("py ")
        or t == "py"
        or t.startswith("ide ")
        or t == "ide"
        or t.startswith("/pythonide")
        or t == "/pythonide"
        or t.startswith("/deepinfer")
        or t == "deepinfer"
        or t.startswith("deepinfer ")
        or t.startswith("/katex")
        or t == "katex"
        or t.startswith("katex ")
    )


def _strip_verb(text: str) -> str:
    t = (text or "").strip()
    lower = t.lower()
    for v in (
        "/pythonide",
        "/py",
        "/ide",
        "pythonide",
        "py",
        "ide",
        "/deepinfer",
        "deepinfer",
        "/katex",
        "katex",
    ):
        if lower == v:
            # bare /deepinfer or /katex → treat as the command itself
            if v in ("/deepinfer", "deepinfer"):
                return "deepinfer"
            if v in ("/katex", "katex"):
                return "katex"
            return ""
        if lower.startswith(v + " "):
            rest = t[len(v) :].strip()
            if v in ("/deepinfer", "deepinfer"):
                return ("deepinfer " + rest).strip()
            if v in ("/katex", "katex"):
                return ("katex " + rest).strip()
            return rest
    return t


def _traceback_lines(exc: Optional[BaseException] = None) -> List[str]:
    if exc is not None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    else:
        tb = traceback.format_exc()
    out: List[str] = []
    for line in tb.rstrip().splitlines():
        out.append(f"[Traceback] {line}")
    return out


def _parse_call_args(raw: str) -> tuple:
    """Parse trailing args with ast.literal_eval for safety (no exec)."""
    raw = (raw or "").strip()
    if not raw:
        return ()
    try:
        val = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        parts = raw.split()
        out: list = []
        for p in parts:
            try:
                out.append(ast.literal_eval(p))
            except (SyntaxError, ValueError):
                out.append(p)
        return tuple(out)
    if isinstance(val, tuple):
        return val
    return (val,)



def _deepinfer_complete_safe(prompt: str, *, prefer: str = "auto") -> Any:
    """Run accelerator.complete with a hard wall clock so chat UI never hangs."""
    import concurrent.futures

    from engine.deepinfer_accelerator import complete

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(complete, prompt, prefer=prefer)
        try:
            return fut.result(timeout=5.0)
        except concurrent.futures.TimeoutError as exc:
            raise TimeoutError(
                "deepinfer.complete exceeded 5s — chatbox refuses to hang"
            ) from exc


def handle_deepinfer(rest: str = "") -> List[str]:
    """Surface DeepInfer accelerator status / probe into chat with traceback."""
    lines: List[str] = []
    parts = (rest or "").split(None, 1)
    # Empty rest (bare /py deepinfer) → demo = status + probe for chatbox showcase
    sub = parts[0].lower() if parts and parts[0] else "status"
    prompt = parts[1] if len(parts) > 1 else "TeaVM CLI deepinfer probe"
    if sub in {"help", "?"}:
        lines.append("[System] deepinfer · optional accelerator (engine/deepinfer_accelerator.py)")
        lines.append("[Engine] /py deepinfer [status|probe|complete] [prompt…]")
        lines.append("[Engine] alias: /deepinfer · Traceback on import/runtime failure")
        return lines
    try:
        from engine.deepinfer_accelerator import (
            deepinfer_available,
            deepinfer_status,
        )

        status = deepinfer_status()
        lines.append(
            "[Engine] deepinfer available="
            + str(status.get("available"))
            + " · role="
            + str(status.get("role"))
            + " · accel_env="
            + str(status.get("accelerator_env"))
        )
        if status.get("import_error"):
            lines.append("[System] import_error: " + str(status["import_error"]))
            # Still emit a traceback-shaped block so chat history shows failure path
            try:
                raise ModuleNotFoundError(str(status["import_error"]))
            except ModuleNotFoundError as exc:
                lines.extend(_traceback_lines(exc))
        if sub in {"status", "stat", "info"}:
            lines.append("[Engine] " + json.dumps(status, default=str)[:1200])
            return lines
        if sub in {"demo", "all"}:
            lines.append("[Engine] " + json.dumps(status, default=str)[:1200])
            try:
                result = _deepinfer_complete_safe(
                    "CLI chatbox deepinfer demo", prefer="auto"
                )
                lines.append(
                    "[Engine] deepinfer.probe → "
                    + json.dumps(result, default=str)[:1200]
                )
            except Exception as probe_exc:  # noqa: BLE001
                lines.append(
                    f"[System] deepinfer.probe skipped: {type(probe_exc).__name__}: {probe_exc}"
                )
                lines.extend(_traceback_lines(probe_exc))
            if not deepinfer_available():
                lines.append(
                    "[System] DeepInfer package absent — fell back to sovereign/offline path"
                )
            return lines
        if sub in {"probe", "complete", "run", "infer"}:
            result = _deepinfer_complete_safe(prompt if sub != "probe" else prompt, prefer="auto")
            rendered = json.dumps(result, default=str)
            lines.append(f"[Engine] deepinfer.{sub} → {rendered[:1500]}")
            if not deepinfer_available() and result.get("mode") in {
                "offline_echo",
                "deepseek",
                None,
            }:
                lines.append(
                    "[System] DeepInfer package absent — fell back to sovereign/offline path"
                )
            return lines
        # treat unknown sub as prompt for complete
        result = _deepinfer_complete_safe(rest.strip() or prompt, prefer="auto")
        lines.append("[Engine] deepinfer.complete → " + json.dumps(result, default=str)[:1500])
        return lines
    except Exception as exc:  # noqa: BLE001
        lines.append(f"[System] deepinfer error: {type(exc).__name__}: {exc}")
        lines.extend(_traceback_lines(exc))
        return lines


def _validate_katex_python_mirror(yaml_path: Path) -> List[str]:
    """Mirror KaTeXTreeValidator + KaTeXMacroSetTest checks in pure Python."""
    import re

    lines_out: List[str] = []
    content = yaml_path.read_text(encoding="utf-8")
    macro_re = re.compile(
        r'^\s*"(\\{1,2}[A-Za-z]+)"\s*:\s*(?:"([^"]*)"|\[\s*"([^"]*)")'
    )
    domain_re = re.compile(r"^([a-z]+):$")
    ref_re = re.compile(r"(\\{1,2}[A-Za-z]+)")

    def norm(raw: str) -> str:
        return "\\" + raw.replace("\\", "")

    macro_map: dict[str, str] = {}
    domain_of: dict[str, str] = {}
    pending: list[tuple[str, str]] = []
    current = "root"
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or trimmed in {"katex:", "macros:"}:
            continue
        dm = domain_re.match(trimmed)
        if dm:
            current = dm.group(1)
            continue
        m = macro_re.match(line)
        if not m:
            continue
        key = norm(m.group(1))
        expansion = m.group(2) if m.group(2) is not None else m.group(3)
        if expansion is None:
            raise AssertionError(f"Missing expansion for {key}")
        if current == "root":
            raise AssertionError(f"Macro outside domain (math|garden|physics): {key}")
        if key in macro_map:
            raise AssertionError(
                f"Duplicate macro definition: {key} in domain {current} "
                f"(already in {domain_of[key]})"
            )
        macro_map[key] = expansion
        domain_of[key] = current
        pending.append((key, expansion))

    graph: dict[str, list[str]] = {}
    for key, expansion in pending:
        deps: list[str] = []
        for rm in ref_re.finditer(expansion):
            dep = norm(rm.group(1))
            if dep == key:
                raise AssertionError(f"Self-referential macro expansion: {key}")
            if dep in macro_map:
                deps.append(dep)
        graph[key] = deps

    visited: set[str] = set()
    stack: set[str] = set()

    def cycle(node: str) -> bool:
        if node in stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for n in graph.get(node, []):
            if cycle(n):
                return True
        stack.remove(node)
        return False

    for node in graph:
        if cycle(node):
            raise AssertionError(f"Cyclic macro dependency detected involving: {node}")

    # KaTeXMacroSetTest.darkLambdaIsPresent
    if '"\\\\darklambda"' not in content and '"\\darklambda"' not in content:
        # YAML often stores as "\\darklambda"
        if "darklambda" not in content:
            raise AssertionError("\\darklambda must be present")
    if "garden:" not in content:
        raise AssertionError("garden domain must be present")

    lines_out.append(
        f"[Engine] Strict KaTeX Tree Validated. Total Macros: {len(macro_map)}"
    )
    lines_out.append(
        "[Engine] KaTeXMacroSetTest.strictTreeIsValid · PASSED (python mirror)"
    )
    lines_out.append(
        "[Engine] KaTeXMacroSetTest.darkLambdaIsPresent · PASSED (python mirror)"
    )
    domains = sorted(set(domain_of.values()))
    lines_out.append("[Engine] domains: " + ", ".join(domains))
    return lines_out


def handle_katex(rest: str = "") -> List[str]:
    """Run KaTeXMacroSetTest (mvn) or python mirror; emit chat + Traceback."""
    lines: List[str] = []
    sub = (rest or "").strip().lower()
    if sub in {"help", "?"}:
        lines.append("[System] KaTeXMacroSetTest · docs/katex_macros.yaml strict tree")
        lines.append(
            "[Engine] /py katex | /py katex_test | /katex · "
            "mvn test -Dtest=KaTeXMacroSetTest (fallback: python mirror)"
        )
        return lines

    yaml_path = _REPO_ROOT / "docs" / "katex_macros.yaml"
    lines.append("[Engine] KaTeXMacroSetTest · path=" + str(yaml_path))

    # Prefer real Maven Surefire when available
    import shutil
    import subprocess

    mvn = shutil.which("mvn")
    if mvn is None and (_REPO_ROOT / "mvnw").exists():
        mvn = str(_REPO_ROOT / "mvnw")
    if mvn:
        lines.append(f"[Engine] running: {mvn} test -Dtest=KaTeXMacroSetTest")
        try:
            proc = subprocess.run(
                [mvn, "-q", "test", "-Dtest=KaTeXMacroSetTest"],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            for raw in combined.splitlines()[-80:]:
                tag = "[Engine]" if proc.returncode == 0 else "[System]"
                if "FAILURE" in raw or "ERROR" in raw or "Exception" in raw:
                    tag = "[Traceback]" if "at " in raw or "Exception" in raw else "[System]"
                lines.append(f"{tag} {raw}")
            if proc.returncode == 0:
                lines.append("[Engine] KaTeXMacroSetTest · BUILD SUCCESS (mvn)")
            else:
                lines.append(
                    f"[System] KaTeXMacroSetTest · mvn exit={proc.returncode}"
                )
                try:
                    raise RuntimeError(
                        f"mvn test -Dtest=KaTeXMacroSetTest failed with exit {proc.returncode}"
                    )
                except RuntimeError as exc:
                    lines.extend(_traceback_lines(exc))
            return lines
        except Exception as exc:  # noqa: BLE001
            lines.append(f"[System] mvn invoke failed: {type(exc).__name__}: {exc}")
            lines.extend(_traceback_lines(exc))
            lines.append("[System] falling back to python mirror of KaTeXTreeValidator")

    lines.append("[System] mvn not on PATH — python mirror of KaTeXMacroSetTest")
    try:
        if not yaml_path.is_file():
            raise FileNotFoundError(f"missing {yaml_path}")
        lines.extend(_validate_katex_python_mirror(yaml_path))
        lines.append("[Engine] Tests run: 2, Failures: 0, Errors: 0 (mirror)")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"[System] KaTeXMacroSetTest FAILED: {type(exc).__name__}: {exc}")
        lines.extend(_traceback_lines(exc))
    return lines


def handle_pythonide(text: str) -> List[str]:
    """Run a pythonIDE CLI command; always returns chat-tagged lines."""
    lines: List[str] = []
    rest = _strip_verb(text)
    if not rest or rest.lower() in {"help", "?"}:
        lines.append("[System] pythonIDE CLI · toolkit.py + pointer_2300")
        lines.append(
            "[Engine] commands: help | list | call <cap> [args] | pointer | "
            "deepinfer | katex"
        )
        lines.append(f"[Engine] dial {LOOPBACK_HOST}:{CLI_PORT}/cli · NO_LEDGER_WRITE")
        lines.append(
            "[Engine] demos: /py deepinfer · /py katex (KaTeXMacroSetTest) · Traceback on fail"
        )
        return lines

    parts = rest.split(None, 2)
    cmd = parts[0].lower()

    try:
        if cmd in {"deepinfer", "di"}:
            sub = rest.split(None, 1)[1] if len(rest.split(None, 1)) > 1 else ""
            return handle_deepinfer(sub)

        if cmd in {"katex", "katex_test", "katexmacrosettest", "macros"}:
            sub = rest.split(None, 1)[1] if len(rest.split(None, 1)) > 1 else ""
            return handle_katex(sub)

        if cmd in {"list", "ls"}:
            from pythonIDE.toolkit import SovereignToolkit

            tk = SovereignToolkit()
            caps = tk.list()
            lines.append(f"[Engine] pythonIDE toolkit · {tk.count()} capabilities")
            lines.append("[Engine] " + ", ".join(caps))
            stubs = tk.stubs()
            if stubs:
                lines.append("[System] stubs: " + ", ".join(stubs))
            return lines

        if cmd in {"pointer", "2300"}:
            from pythonIDE.pointer_2300 import pointer_payload

            payload = pointer_payload()
            lines.append(
                f"[Engine] pointer {payload.get('pointer_id')} → "
                f"Context Layer {payload.get('context_layer')} · {payload.get('domain')}"
            )
            lines.append(
                "[Engine] author="
                + str(payload.get("author"))
                + " · anchor="
                + str(payload.get("anchors", {}).get("anchor", ""))
            )
            lines.append("[Engine] " + json.dumps(payload, sort_keys=True)[:1500])
            return lines

        if cmd in {"call", "run"}:
            if len(parts) < 2:
                raise TypeError("call requires capability name — /py call <name> [args]")
            name = parts[1]
            arg_raw = parts[2] if len(parts) > 2 else ""
            args = _parse_call_args(arg_raw)
            from pythonIDE.toolkit import SovereignToolkit

            tk = SovereignToolkit()
            result = tk.call(name, *args)
            rendered = result if isinstance(result, str) else json.dumps(result, default=str)
            lines.append(f"[Engine] {name} → {rendered}")
            return lines

        from pythonIDE.toolkit import SovereignToolkit

        tk = SovereignToolkit()
        if cmd in tk.list():
            result = tk.call(cmd)
            rendered = result if isinstance(result, str) else json.dumps(result, default=str)
            lines.append(f"[Engine] {cmd} → {rendered}")
            return lines

        raise ValueError(
            f"unknown ide command: {cmd} — try /py help | /py list | /py call <cap> | /py pointer"
        )
    except Exception as exc:  # noqa: BLE001 — surface full traceback to chat UI
        lines.append(f"[System] pythonIDE error: {type(exc).__name__}: {exc}")
        lines.extend(_traceback_lines(exc))
        return lines


def create_app():
    """Build the FastAPI app (import fastapi only when serving)."""
    from fastapi import FastAPI, WebSocketDisconnect
    if FastAPIWebSocket is None:
        raise ModuleNotFoundError("fastapi.WebSocket unavailable")

    app = FastAPI(title="Sovereign IRC CLI loopback", version="0.2.0")

    @app.get("/health")
    async def health() -> dict:
        return {
            "service": "sovereign-irc-bridge-cli",
            "bind": f"{LOOPBACK_HOST}:{CLI_PORT}",
            "path": "/cli",
            "remote": REMOTE_IRC,
            "live_irc": os.environ.get("CLI_LIVE_IRC", "0") == "1",
            "pythonide": True,
            "demos": ["deepinfer", "katex"],
            "llm": os.environ.get("LLM_URL", "http://127.0.0.1:8081/v1/chat/completions"),
            "llm_backend": _llm_backend_health(),
        }

    @app.websocket("/cli")
    async def cli_socket(websocket: FastAPIWebSocket) -> None:
        try:
            await websocket.accept()
        except Exception as exc:  # noqa: BLE001
            # Handshake already failed — nothing to send; log for operators
            logger.exception("cli websocket accept failed: %s", exc)
            return
        await websocket.send_text(f"[System] loopback CLI on {LOOPBACK_HOST}:{CLI_PORT}/cli")
        await websocket.send_text(f"[Engine] path → {REMOTE_IRC} (browser never dials abjects)")
        await websocket.send_text(
            "[Engine] pythonIDE: /py help · /py list · /py call <cap> · /py pointer"
        )
        await websocket.send_text(
            "[Engine] demos: /py deepinfer · /py katex (KaTeXMacroSetTest) · Traceback on fail"
        )
        await websocket.send_text(
            "[Engine] llm: /llm <text> → GGUF llama-server (loopback) with spike snapshot + traceback feedback"
        )
        live = os.environ.get("CLI_LIVE_IRC", "0") == "1"
        reader = writer = None
        if live:
            host, _, port_s = REMOTE_IRC.partition(":")
            try:
                reader, writer = await asyncio.open_connection(host, int(port_s))
                await websocket.send_text(f"[Engine] live TCP open → {REMOTE_IRC}")
            except Exception as exc:  # noqa: BLE001 — surface to CLI UI
                await websocket.send_text(f"[System] live TCP failed: {exc} · staying stub")
                for line in _traceback_lines(exc):
                    await websocket.send_text(line)
                reader = writer = None
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                text = message.get("text")
                if text is None and message.get("bytes") is not None:
                    text = message["bytes"].decode("utf-8", errors="replace")
                if not text:
                    continue
                if is_llm_line(text):
                    try:
                        llm_lines = await handle_llm(text)
                    except Exception as exc:  # noqa: BLE001 — chat must survive
                        llm_lines = [f"[System] llm offline: {type(exc).__name__}: {exc}"]
                    for line in llm_lines:
                        await websocket.send_text(line)
                    continue
                if _is_ide_line(text):
                    for line in handle_pythonide(text):
                        await websocket.send_text(line)
                    continue
                await websocket.send_text(f"[Engine] ack: {text}")
                if writer is not None:
                    writer.write((text.rstrip("\r\n") + "\r\n").encode("utf-8"))
                    await writer.drain()
                    if reader is not None:
                        try:
                            chunk = await asyncio.wait_for(reader.read(4096), timeout=0.4)
                            if chunk:
                                await websocket.send_text(
                                    "[Engine] "
                                    + chunk.decode("utf-8", errors="replace").rstrip()
                                )
                        except asyncio.TimeoutError:
                            pass
        except WebSocketDisconnect:
            pass
        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    return app


# ASGI entry used by uvicorn / Dockerfile when fastapi is installed.
try:
    app = create_app()
except ModuleNotFoundError:
    app = None  # type: ignore[assignment]


def _llm_backend_health() -> dict:
    from src import llm_backend

    return llm_backend.health_blob()


def run() -> None:
    import uvicorn

    from src import llm_backend

    try:
        host = assert_loopback_bind(os.environ.get("CLI_BIND_HOST", LOOPBACK_HOST))
        assert_loopback_url(
            os.environ.get("LLM_URL", "http://127.0.0.1:8081/v1/chat/completions")
        )
        # DeepInfer is held to the same loopback rule as LLM_URL.
        assert_loopback_url(llm_backend.deepinfer_url_raw(), "DEEPINFER_URL")
        assert_loopback_url(llm_backend.deepseek_url_raw(), "LLM_DEEPSEEK_URL")
        backend = llm_backend.backend()
        fallback = llm_backend.fallback()
    except (RuntimeError, LlmConfigError, llm_backend.BackendConfigError) as exc:
        # Same as tools/cors-anywhere: refuse non-loopback, exit non-zero.
        print(f"FATAL: Cosmic Alignment — {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    # Template family + ChatML prebuild tokenization check; logs, never raises.
    from src import chatml_prebuild

    llm_url_env = os.environ.get("LLM_URL", "http://127.0.0.1:8081/v1/chat/completions")
    # One "[System] llm backend: …" line (DeepInfer liveness + deep_gemm/deep_ep/CUDA);
    # it also fills the liveness cache so the first /llm never waits on a dead port.
    print(llm_backend.startup_probe(llm_url_env), file=sys.stderr, flush=True)
    if "gguf" in (backend, fallback):
        chatml_prebuild.startup_check(llm_url_env)
    if "deepseek-fixture" in (backend, fallback):
        chatml_prebuild.startup_check(llm_backend.deepseek_url_raw())
    port = int(os.environ.get("CLI_BIND_PORT", str(CLI_PORT)))
    if port != CLI_PORT:
        logger.warning("non-default CLI port %s (contract is %s)", port, CLI_PORT)
    logger.info("CLI loopback bind %s:%s /cli → remote %s", host, port, REMOTE_IRC)
    uvicorn.run(
        "src.cli_loopback:app",
        host=host,
        port=port,
        log_level=os.environ.get("DEPLOY_LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run()
