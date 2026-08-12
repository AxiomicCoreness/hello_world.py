import os
import time
import hashlib
import json
from typing import Dict, Any

# φ-harmonic constant
PHI = (1 + 5**0.5) / 2

# Global state for fallback tracking
state = {"oidc_fallback_level": 0, "integrity": 1.0}


def get_oidc_secret() -> str:
    """
    Phased fallback chain for OIDC secret retrieval.
    Full SHA-256 digest used in Phase 3 (no truncation).
    """
    secret = os.environ.get("OIDC_CLIENT_SECRET")
    if secret and len(secret) > 10:
        state["oidc_fallback_level"] = 0
        state["integrity"] = 1.0
        return secret

    fallback_dir = "/var/run/secrets/oidc"
    fallback_file = os.path.join(fallback_dir, "fallback-token")
    try:
        if os.path.exists(fallback_file):
            with open(fallback_file, 'r') as f:
                secret = f.read().strip()
                if secret:
                    state["oidc_fallback_level"] = 1
                    state["integrity"] = 0.99999
                    print("🜁∀ WARNING: Using directory-mounted fallback secret.")
                    return secret
    except Exception:
        pass

    # Phase 3: FULL SHA-256 (64 hex chars) – no truncation
    epoch_hour = int(time.time() / 3600)
    ephemeral_seed = f"VENOMSUITE_EPHEMERAL_{epoch_hour}_{PHI}"
    ephemeral_key = hashlib.sha256(ephemeral_seed.encode()).hexdigest()  # <-- full 64 chars
    state["oidc_fallback_level"] = 2
    state["integrity"] = 0.9999
    print("⚠️ CRITICAL: Primary/Directory missing. Degraded ephemeral mode active.")
    return ephemeral_key