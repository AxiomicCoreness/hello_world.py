# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Real time + web tools for the v3t route: ``now_line``, ``web_fetch``, ``web_search``.

Tool calls use the Qwen format v3t already knows::

    <tool_call>{"name": "web_fetch", "arguments": {"url": "https://example.com"}}</tool_call>

Outbound safety (SSRF): http(s) only; no userinfo; every resolved address and the
actually-connected peer must be public (loopback, private, link-local, CGNAT,
multicast, reserved and unspecified are blocked); each redirect hop is re-checked;
response capped (``MAX_BYTES``) with a timeout; requests carry only a User-Agent
(no cookies, no auth, no secrets). ``V3T_FETCH_ALLOW_NETS`` (comma CIDRs) is an
explicit opt-in for a sandbox whose resolver maps every name into a reserved
range (e.g. 198.18.0.0/15); it never re-allows loopback.
"""
from __future__ import annotations

import html
import http.client
import ipaddress
import json
import os
import re
import socket
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover - tzdata missing
    NY = None

MAX_BYTES = 512 * 1024
MAX_TEXT = 4000
TIMEOUT_S = 10.0
MAX_REDIRECTS = 4
UA = "ClarkeYoursaTee-v3t-route/1 (+https://github.com/AxiomicCoreness/hello_world.py)"
SEARCH_URL = "https://html.duckduckgo.com/html/?q="
TOOL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)

TOOLS_PROMPT = (
    "\nYou can use two tools. To use one, reply with ONLY a tool call line, then wait for the "
    "<tool_response>:\n"
    '<tool_call>{"name": "web_search", "arguments": {"query": "..."}}</tool_call>\n'
    '<tool_call>{"name": "web_fetch", "arguments": {"url": "https://..."}}</tool_call>\n'
    "Example:\nuser: What is on https://example.com?\n"
    'assistant: <tool_call>{"name": "web_fetch", "arguments": {"url": "https://example.com"}}</tool_call>\n'
    "user: <tool_response>Example Domain. This domain is for use in documentation examples.</tool_response>\n"
    "assistant: The page is the Example Domain placeholder used in documentation examples.\n"
    "Use the current time line for dates and times; use tools only for web content."
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def now_line(now: Optional[datetime] = None) -> str:
    """'Current time: 2026-11-02T15:30:00-05:00 (UTC 2026-11-02T20:30:00Z). …' — fresh each call."""
    now = (now or utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    local = now.astimezone(NY) if NY else now
    return (f"Current time: {local.isoformat()} (UTC {now.strftime('%Y-%m-%dT%H:%M:%SZ')}). "
            "Always write timestamps in ISO 8601 with explicit offset.")


class BlockedURL(ValueError):
    pass


def _allow_nets() -> List[ipaddress._BaseNetwork]:
    out = []
    for c in (os.environ.get("V3T_FETCH_ALLOW_NETS") or "").split(","):
        c = c.strip()
        if c:
            out.append(ipaddress.ip_network(c, strict=False))
    return out


def ip_allowed(ip: str) -> bool:
    a = ipaddress.ip_address(ip.split("%")[0])
    if isinstance(a, ipaddress.IPv6Address) and a.ipv4_mapped:
        a = a.ipv4_mapped
    if a.is_loopback or a.is_unspecified or a.is_multicast or a.is_link_local:
        return False
    if a.is_global:
        return True
    return any(a in n for n in _allow_nets())


def check_url(url: str, resolver: Callable = socket.getaddrinfo) -> Tuple[str, str, int]:
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https"):
        raise BlockedURL("only http(s) URLs")
    if p.username or p.password or not p.hostname:
        raise BlockedURL("no host / userinfo not allowed")
    port = p.port or (443 if p.scheme == "https" else 80)
    try:
        infos = resolver(p.hostname, port, proto=socket.IPPROTO_TCP)
    except OSError as e:
        raise BlockedURL(f"cannot resolve {p.hostname}: {e}")
    addrs = {i[4][0] for i in infos}
    if not addrs or not all(ip_allowed(x) for x in addrs):
        raise BlockedURL(f"{p.hostname} resolves to a non-public address")
    return p.scheme, p.hostname, port


def _peer_check(sock: socket.socket) -> None:
    peer = sock.getpeername()[0]
    if not ip_allowed(peer):
        sock.close()
        raise BlockedURL("connected peer is not a public address")


class _HTTP(http.client.HTTPConnection):
    def connect(self):
        super().connect()
        _peer_check(self.sock)


class _HTTPS(http.client.HTTPSConnection):
    def connect(self):
        super().connect()
        _peer_check(self.sock)


class _H(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_HTTP, req)


class _HS(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_HTTPS, req, context=self._context)


class _Redir(urllib.request.HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_H, _HS, _Redir)
for _h in list(_OPENER.handlers):  # no proxies / cookies from the environment
    if isinstance(_h, urllib.request.ProxyHandler):
        _OPENER.handlers.remove(_h)


def _to_text(raw: bytes, ctype: str) -> str:
    t = raw.decode("utf-8", "replace")
    if "html" in ctype or "<html" in t[:500].lower():
        t = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", t)
        t = re.sub(r"(?s)<[^>]+>", " ", t)
        t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def web_fetch(url: str, *, opener=None, timeout: float = TIMEOUT_S) -> str:
    check_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,text/plain,*/*"})
    with (opener or _OPENER).open(req, timeout=timeout) as r:
        raw = r.read(MAX_BYTES + 1)[:MAX_BYTES]
        ctype = r.headers.get("Content-Type", "")
    return _to_text(raw, ctype)[:MAX_TEXT]


def web_search(query: str, *, fetch=None) -> str:
    q = (query or "").strip()[:300]
    if not q:
        return "empty query"
    url = SEARCH_URL + urllib.parse.quote_plus(q)
    check_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with (fetch or _OPENER).open(req, timeout=TIMEOUT_S) as r:
        page = r.read(MAX_BYTES).decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</', page, re.S):
        href = html.unescape(m.group(1))
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(href).query)
        href = qs.get("uddg", [href])[0]
        title = _to_text(m.group(2).encode(), "html")
        snip = _to_text(m.group(3).encode(), "html")
        out.append(f"{len(out)+1}. {title} — {href}\n   {snip}")
        if len(out) >= 5:
            break
    return "\n".join(out) if out else "no results"


def parse_tool_call(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    m = TOOL_RE.search(text or "")
    if not m:
        return None
    try:
        d = json.loads(m.group(1))
        name, args = d.get("name"), d.get("arguments") or {}
        if isinstance(args, str):
            args = json.loads(args)
    except Exception:
        return None
    if name in ("web_fetch", "web_search") and isinstance(args, dict):
        return name, args
    return None


def run_tool(name: str, args: Dict[str, Any], tools: Optional[Dict[str, Callable]] = None) -> str:
    fns = tools or {"web_fetch": lambda a: web_fetch(str(a.get("url", ""))),
                    "web_search": lambda a: web_search(str(a.get("query", "")))}
    try:
        return fns[name](args)
    except BlockedURL as e:
        return f"blocked: {e}"
    except Exception as e:  # network errors etc. — reported to the model, never raised
        return f"error: {type(e).__name__}: {e}"[:300]
