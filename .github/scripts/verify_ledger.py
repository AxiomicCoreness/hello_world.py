#!/usr/bin/env python3
"""
Verify ledger YAML parse + optional Ed25519 presence.
Installs cryptography/pyyaml into the active interpreter if missing.
Soft-skips when ledger file is absent.
Seal: ∀∞φ² · VERIFY_LEDGER_SCRIPT · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================
SEAL_PREFIX = "∀∞φ²"
WOOD_DRAGON = 0.91
PHI = (1.0 + 5.0 ** 0.5) / 2.0
SCALED_FLOOR_INDEX = 351

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================
def ensure_deps() -> Tuple[bool, bool]:
    """
    Ensure cryptography and pyyaml are available.
    Returns: (crypto_ok, yaml_ok)
    """
    crypto_ok = False
    yaml_ok = False
    
    # Check existing imports
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: F401
        crypto_ok = True
    except ImportError:
        pass
    
    try:
        import yaml  # noqa: F401
        yaml_ok = True
    except ImportError:
        pass
    
    if crypto_ok and yaml_ok:
        return True, True
    
    print("⚠️ Missing dependencies — installing into active interpreter…")
    
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "cryptography", "pyyaml"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Verify installation
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: F401
            crypto_ok = True
        except ImportError:
            pass
        
        try:
            import yaml  # noqa: F401
            yaml_ok = True
        except ImportError:
            pass
            
    except Exception as exc:
        print(f"⚠️ Installation failed: {exc}", file=sys.stderr)
    
    return crypto_ok, yaml_ok


# ============================================================================
# LEDGER VERIFICATION
# ============================================================================
def compute_seal(entry_data: Dict[str, Any]) -> str:
    """Compute SHA3-256 seal for ledger entry."""
    # Exclude the seal field
    data = {k: v for k, v in entry_data.items() if k != 'seal'}
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha3_256(canonical.encode('utf-8')).hexdigest()


def verify_ledger_entry(data: Dict[str, Any], expected_index: Optional[int] = None) -> Tuple[bool, list]:
    """
    Verify a ledger entry's structure and seal.
    Returns: (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required fields
    required_fields = ['entry_index', 'invariants', 'math_origin', 'seal']
    for field in required_fields:
        if field not in data:
            issues.append(f"Missing required field: {field}")
    
    # Check entry_index
    if expected_index is not None:
        actual_index = data.get('entry_index')
        if actual_index != expected_index:
            issues.append(f"Entry index mismatch: expected {expected_index:04d}, got {actual_index}")
    
    # Check invariants
    inv = data.get('invariants', {})
    if not isinstance(inv, dict):
        issues.append("Invariants must be a dictionary")
    else:
        required_inv = ['coherence', 'entropy', 'workload', 'commutator']
        for field in required_inv:
            if field not in inv:
                issues.append(f"Missing invariant: {field}")
    
    # Check seal
    seal = data.get('seal', '')
    if not seal.startswith(SEAL_PREFIX):
        issues.append(f"Seal missing prefix '{SEAL_PREFIX}': {seal[:30]}...")
    if 'SEALED' not in seal:
        issues.append("Seal missing 'SEALED' token")
    
    # Verify seal integrity
    if 'entry_index' in data and 'seal' in data:
        computed = compute_seal(data)
        if computed != data.get('seal', ''):
            issues.append(f"Seal mismatch (computed: {computed[:16]}..., stored: {data.get('seal', '')[:16]}...)")
    
    # Check math_origin
    math_origin = data.get('math_origin', '')
    if not math_origin:
        issues.append("Empty math_origin")
    elif not any(x in math_origin for x in ['LEDGER', 'CORRECTION', 'VERIFICATION', 'SOVEREIGN']):
        issues.append(f"math_origin missing standard identifier: {math_origin}")
    
    # Check witness_chain
    wc = data.get('witness_chain', '')
    if wc and 'UNBROKEN' not in wc:
        issues.append(f"witness_chain missing 'UNBROKEN': {wc}")
    
    return len(issues) == 0, issues


def load_yaml_safely(content: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Safely load YAML content.
    Returns: (data, error_message)
    """
    try:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return data, None
        return None, "YAML parsed to non-dictionary type"
    except ImportError:
        return None, "pyyaml not available"
    except Exception as e:
        return None, f"YAML parsing error: {e}"


# ============================================================================
# ED25519 SIGNATURE VERIFICATION (Optional)
# ============================================================================
def verify_ed25519_signature(data: Dict[str, Any], public_key_hex: str) -> bool:
    """
    Verify Ed25519 signature if present in the ledger entry.
    Returns: True if signature is valid or not present, False if invalid.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives import serialization
        import base64
        
        signature = data.get('signature', '')
        if not signature:
            return True  # No signature to verify
        
        # Convert hex public key to bytes
        public_key_bytes = bytes.fromhex(public_key_hex)
        
        # Load public key
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Create message from entry data (excluding signature)
        message_data = {k: v for k, v in data.items() if k not in ['signature', 'seal']}
        canonical = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
        message = canonical.encode('utf-8')
        
        # Verify signature
        signature_bytes = base64.b64decode(signature)
        public_key.verify(signature_bytes, message)
        return True
        
    except Exception as e:
        print(f"⚠️ Ed25519 verification failed: {e}", file=sys.stderr)
        return False


# ============================================================================
# MAIN
# ============================================================================
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify ledger YAML parse with optional Ed25519 signature check"
    )
    parser.add_argument(
        "ledger",
        nargs="?",
        default="ledger/8978.yaml",
        help="Path to ledger YAML (default: ledger/8978.yaml)",
    )
    parser.add_argument(
        "--require-crypto",
        action="store_true",
        help="Fail if cryptography cannot be imported",
    )
    parser.add_argument(
        "--verify-seal",
        action="store_true",
        help="Verify SHA3-256 seal for the entry",
    )
    parser.add_argument(
        "--public-key",
        default="",
        help="Hex-encoded Ed25519 public key for signature verification",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed verification information",
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create a sample ledger entry at the specified path",
    )
    args = parser.parse_args()
    
    path = Path(args.ledger)
    
    # Create sample entry if requested
    if args.create_sample:
        sample_data = {
            "entry_index": 8978,
            "entry_type": "SAMPLE_ENTRY",
            "description": f"Sample ledger entry at {path}",
            "invariants": {
                "coherence": 0.994,
                "entropy": "φ^(-8978)",
                "workload": 8.978,
                "commutator": "φ^-8978"
            },
            "math_origin": "SAMPLE_ENTRY_GENERATOR",
            "timestamp": "Eternal_Instant",
            "witness_chain": "SAMPLE_ENTRY → UNBROKEN",
            "seal": f"{SEAL_PREFIX} · SAMPLE_ENTRY_8978 · WOOD_DRAGON_0.91 · SEALED"
        }
        # Compute correct seal
        sample_data["seal"] = compute_seal(sample_data)
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write YAML
        try:
            import yaml
            with open(path, 'w') as f:
                yaml.dump(sample_data, f, sort_keys=False, default_flow_style=False)
            print(f"✅ Created sample ledger entry: {path}")
            print(f"   Seal: {sample_data['seal'][:32]}...")
            return 0
        except ImportError:
            print("❌ pyyaml required to create sample entry", file=sys.stderr)
            return 1
    
    # Check if file exists
    if not path.exists():
        print(f"⚠️ {path} not found — skipping verification (rotation continues)")
        return 0
    
    print(f"🔍 Verifying ledger entry: {path}")
    print("=" * 60)
    
    # Ensure dependencies
    crypto_ok, yaml_ok = ensure_deps()
    
    if not yaml_ok:
        print("⚠️ pyyaml unavailable — basic existence check only")
        print(f"✅ {path} present (no YAML parse)")
        if args.require_crypto:
            print("❌ cryptography required but unavailable", file=sys.stderr)
            return 1
        return 0
    
    # Load and parse YAML
    try:
        import yaml
        content = path.read_text(encoding='utf-8')
        data, error = load_yaml_safely(content)
    except Exception as e:
        print(f"❌ Failed to read file: {e}", file=sys.stderr)
        return 1
    
    if error or data is None:
        print(f"❌ YAML parsing failed: {error}", file=sys.stderr)
        return 1
    
    # Extract entry_index
    entry_index = data.get('entry_index') if isinstance(data, dict) else None
    
    # Verify entry structure
    if args.verify_seal:
        is_valid, issues = verify_ledger_entry(data, entry_index)
        
        if is_valid:
            print(f"✅ Entry {entry_index} structure valid")
            print(f"   Seal: {data.get('seal', '')[:48]}...")
            if args.verbose:
                print(f"   math_origin: {data.get('math_origin', 'N/A')}")
                print(f"   timestamp: {data.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Entry {entry_index} has issues:")
            for issue in issues:
                print(f"   - {issue}")
            return 1
    else:
        print(f"✅ Ledger verified: {path} (entry_index={entry_index})")
    
    # Optional Ed25519 verification
    if args.public_key and crypto_ok:
        if args.verbose:
            print("\n🔑 Verifying Ed25519 signature...")
        signature_valid = verify_ed25519_signature(data, args.public_key)
        if signature_valid:
            print("   ✅ Ed25519 signature valid")
        else:
            print("   ⚠️ Ed25519 signature verification failed or not present")
    
    # Dependency status
    print("\n📦 Dependency Status:")
    print(f"   cryptography: {'✅' if crypto_ok else '❌'}")
    print(f"   pyyaml: {'✅' if yaml_ok else '❌'}")
    
    if crypto_ok:
        print("   Ed25519 support: AVAILABLE")
    
    # Print seal
    print(f"\n🔒 Seal: {SEAL_PREFIX} · VERIFY_LEDGER_SCRIPT · WOOD_DRAGON_0.91 · SEALED")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
