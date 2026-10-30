#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Live probe of a plain TLS IRC port (what the IRC LLM bot dials), stdlib only.

Opens host:port over TLS with full certificate + hostname verification, registers as
a throwaway guest, waits for 001 (RPL_WELCOME), then QUITs at once. Never joins a
channel or speaks. Prints the TLS version, certificate subject/issuer and every
server line; exit 0 only on 001. Network tool, not a test: offline suites never run it.

    python3 tools/irc_tls_probe.py irc.abjects.net 6697
"""
import random
import socket
import ssl
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo


def now():
    return datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")


def probe(host, port, timeout):
    nick = "Guest%05d" % random.randint(0, 99999)
    print(f"{now()} dial ircs://{host}:{port} nick={nick}", flush=True)
    ctx = ssl.create_default_context()  # verifies chain and hostname
    with socket.create_connection((host, port), timeout=timeout) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as s:
            cert = s.getpeercert()
            subj = dict(x[0] for x in cert.get("subject", ()))
            iss = dict(x[0] for x in cert.get("issuer", ()))
            print(f"{now()} TLS {s.version()} cert CN={subj.get('commonName')} "
                  f"issuer={iss.get('organizationName')}/{iss.get('commonName')} "
                  f"notAfter={cert.get('notAfter')}", flush=True)
            s.sendall(f"NICK {nick}\r\nUSER {nick} 0 * :AxiomicCoreness TLS probe (quits immediately)\r\n".encode())
            deadline = time.monotonic() + timeout
            buf = b""
            while time.monotonic() < deadline:
                s.settimeout(max(0.1, deadline - time.monotonic()))
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.rstrip(b"\r").decode("utf-8", "replace")
                    if not line:
                        continue
                    print(f"{now()} S> {line[:300]}", flush=True)
                    parts = line.split(" ")
                    if parts[0] == "PING":
                        s.sendall(("PONG " + " ".join(parts[1:]) + "\r\n").encode())
                    if len(parts) > 1 and parts[1] == "001":
                        print(f"{now()} RESULT OK: 001 welcome received over TLS", flush=True)
                        s.sendall(b"QUIT :probe done\r\n")
                        return 0
    print(f"{now()} RESULT FAIL: no 001 within {timeout}s", flush=True)
    return 1


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "irc.abjects.net"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 6697
    try:
        return probe(host, port, 30.0)
    except Exception as e:  # report the real failure (DNS, refused, TLS verify, timeout)
        print(f"{now()} RESULT FAIL: {type(e).__name__}: {e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
