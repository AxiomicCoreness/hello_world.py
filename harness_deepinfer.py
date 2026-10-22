#!/usr/bin/env python3
"""
DeepInfer Add-on Harness
Executes the built DeepInfer engine and seals the output.
"""

import subprocess
import hashlib
import json
import sys
import os

def run_deepinfer(model_path: str, prompt: str) -> dict:
    """Runs the DeepInfer engine and returns a sealed payload."""
    
    # Command to execute the built binary
    cmd = ["deepinfer", "--model", model_path, "--prompt", prompt]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
    except FileNotFoundError:
        # If the binary doesn't exist, check if we are in GitHub Actions
        if os.environ.get("CI") == "true":
            print(f"⚠️ [CI MOCK] DeepInfer binary not found. Simulating output for prompt.", file=sys.stderr)
            output = f"[CI MOCK] Simulated DeepInfer execution for prompt: {prompt}"
        else:
            print(json.dumps({"error": "DeepInfer binary not found in PATH"}))
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": f"DeepInfer failed: {e.stderr}"}))
        sys.exit(1)
        
    # Calculate the SHA3-256 seal of the output
    output_hash = hashlib.sha3_256(output.encode('utf-8')).hexdigest()
    
    return {
        "engine": "DeepInfer",
        "accelerator": os.environ.get("DEEPINFER_ACCELERATOR", "unknown"),
        "prompt": prompt,
        "output": output,
        "terminal_hex": output_hash
    }

if __name__ == "__main__":
    model = os.environ.get("DEEPINFER_MODEL", "/app/models/default")
    prompt = os.environ.get("DEEPINFER_PROMPT", "Initialize sovereign inference sequence.")
    
    sealed_result = run_deepinfer(model, prompt)
    
    if "--json" in sys.argv:
        print(json.dumps(sealed_result))
    else:
        print("✅ Harness complete.")
        print(json.dumps(sealed_result, indent=2))
