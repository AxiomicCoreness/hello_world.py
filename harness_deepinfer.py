import subprocess
import hashlib
import json
import sys
import os

def run_deepinfer(model_path: str, prompt: str) -> dict:
    # Assuming the build script produced a `deepinfer` CLI
    cmd = ["deepinfer", "--model", model_path, "--prompt", prompt]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": f"DeepInfer failed: {e.stderr}"}))
        sys.exit(1)
        
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
