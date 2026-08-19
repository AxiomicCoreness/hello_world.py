import os
import sys
import json
import re
import ssl
import argparse
from pathlib import Path
from typing import Dict, Optional
from fastapi import HTTPException  # only needed if imported as module

# ──────────────────────────────────────────────────────────────────────
# mTLS CONFIGURATION MODULE (embedded)
# ──────────────────────────────────────────────────────────────────────
# When this file is imported, the following constants and functions are available:

SERVER_CERT = os.environ.get("SERVER_CERT", "/certs/server.crt")
SERVER_KEY = os.environ.get("SERVER_KEY", "/certs/server.key")
CA_CERT = os.environ.get("CA_CERT", "/certs/ca.crt")

def get_ssl_context() -> ssl.SSLContext:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(SERVER_CERT, SERVER_KEY)
    ssl_context.load_verify_locations(CA_CERT)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    return ssl_context

def verify_client_cert(request):
    client_cert = getattr(request.client, "cert", None)
    if not client_cert:
        raise HTTPException(status_code=403, detail="mTLS client certificate required")
    return client_cert

# ──────────────────────────────────────────────────────────────────────
# EXTRACTION UTILITY (runs only when __name__ == "__main__")
# ──────────────────────────────────────────────────────────────────────

def find_file(root: Path, filename: str) -> Optional[Path]:
    for p in root.rglob(filename):
        if "certs" not in p.parts and ".git" not in p.parts:
            return p
    return None

def extract_ssl_context(content: str) -> str:
    pattern = r'(ssl_context\s*=\s*ssl\.create_default_context.*?)(?=\n\n|\n\s*[^\s])'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        block = match.group(1)
        uvicorn_pattern = r'(uvicorn\.run\s*\([\s\S]*?ssl_cert_reqs\s*=\s*ssl\.CERT_REQUIRED[\s\S]*?\))'
        uvicorn_match = re.search(uvicorn_pattern, content)
        if uvicorn_match:
            block += "\n\n" + uvicorn_match.group(1)
        return block
    return ""

def extract_function(content: str, func_name: str) -> str:
    pattern = rf'(def\s+{func_name}\s*\([\s\S]*?)(?=\n\s*def|\n\s*@|\n\s*class|\n\n|\Z)'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return ""

def extract_env_vars(content: str) -> Dict[str, str]:
    pattern = r'(SERVER_CERT|SERVER_KEY|CA_CERT)\s*=\s*os\.environ\.get\(["\']([^"\']+)["\']'
    env_vars = {}
    for match in re.finditer(pattern, content):
        var_name = match.group(1)
        default = match.group(2)
        env_vars[var_name] = default
    return env_vars

def extract_and_output(output_format: str = "module") -> None:
    root = Path(__file__).resolve().parent
    port380_path = find_file(root, "port380_mcp.py")
    if not port380_path:
        print("❌ port380_mcp.py not found in repository.")
        sys.exit(1)

    content = port380_path.read_text(encoding="utf-8")

    if output_format == "module":
        # Instead of generating a new module, we just print the embedded version
        print("# 🜁∀ Embedded mTLS module — Entry 8759")
        print("# (To use, import this file directly)")
        print("#")
        print("from mtls_extract_and_config import get_ssl_context, verify_client_cert")
        print()

    elif output_format == "json":
        data = {
            "ssl_context": extract_ssl_context(content),
            "verify_client_cert": extract_function(content, "verify_client_cert"),
            "env_vars": extract_env_vars(content),
        }
        output_path = root / "mtls_extract.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ mTLS extraction written to {output_path}")

    else:
        print("❌ Unknown output format. Use 'module' or 'json'.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified mTLS extraction and config")
    parser.add_argument("--format", choices=["module", "json"], default="module",
                        help="Output format (module or json)")
    parser.add_argument("--extract", action="store_true",
                        help="Extract and output the current configuration (default: just show usage)")
    args = parser.parse_args()

    if args.extract:
        extract_and_output(args.format)
    else:
        print("🜁∀ Unified mTLS Config — Entry 8759")
        print("   This file can be imported to use the mTLS configuration.")
        print("   Run with --extract to extract from port380_mcp.py.")
        print("   Example: python mtls_extract_and_config.py --extract --format json")
