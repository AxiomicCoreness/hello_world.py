"""
Port-380 MCP server.
Binds to $PORT (default 380). Kubernetes-friendly — reads env, exits cleanly on SIGTERM.
"""
import os
import signal
import sys
import json
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", "380"))
NAMESPACE = os.environ.get("NAMESPACE", "seagate-mimic")
MCP_FILLED = os.environ.get("MCP_FILLED", "false").lower() == "true"
LEDGER_HEAD = os.environ.get("LEDGER_HEAD", "9142")


class MCPHandler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "port": PORT, "namespace": NAMESPACE})
        elif self.path == "/pulse":
            self._send(
                200,
                {
                    "mcp": "port380",
                    "filled": MCP_FILLED,
                    "ledger_head": LEDGER_HEAD,
                },
            )
        elif self.path == "/":
            self._send(200, {"mcp": "port380", "status": "listening"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return

        if self.path == "/gate":
            entry = int(data.get("entry", 0))
            event = str(data.get("event", ""))
            # elif dispatch on entry number — never eval
            if entry >= 9200:
                form = "B"
            else:
                form = "A"
            payload = f"{entry}|{event}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462"
            seal = hashlib.sha3_256(payload.encode()).hexdigest()
            self._send(
                200, {"accepted": True, "form": form, "entry": entry, "seal": seal}
            )
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[mcp:{PORT}] {fmt % args}\n")


def shutdown(signum, frame):
    print(f"[mcp] received signal {signum}, shutting down...", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    print(f"[mcp] binding 0.0.0.0:{PORT} namespace={NAMESPACE}", flush=True)
    HTTPServer(("0.0.0.0", PORT), MCPHandler).serve_forever()
