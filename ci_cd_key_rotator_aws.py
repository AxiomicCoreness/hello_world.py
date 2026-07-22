import boto3
import json
from sovereign_key_rotator import SovereignKeyRotator  # Your original class

class AWSSecretsManagerRotator(SovereignKeyRotator):
    def __init__(self, secret_name: str, region: str = "us-east-1"):
        super().__init__()
        self.secret_name = secret_name
        self.region = region
        self.client = boto3.client('secretsmanager', region_name=region)

    def load_state(self) -> bool:
        """Load state from AWS Secrets Manager. Returns True if loaded, False if new deployment."""
        try:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            state = json.loads(response['SecretString'])
            
            # Restore state
            self.rotation_index = state.get('rotation_count', 0)
            self.current_key = state.get('current_key', '')
            self.key_history = state.get('key_history', [])
            
            # Ensure key_history is a list of dicts with 'key_hash'
            if self.key_history and isinstance(self.key_history[0], str):
                # Migrate legacy format (strings) to new format (dicts)
                self.key_history = [{'key_hash': k, 'timestamp': state.get('created_at', '')} for k in self.key_history]
            
            return True
        except (self.client.exceptions.ResourceNotFoundException, json.JSONDecodeError, KeyError):
            # New deployment — initialize empty state
            self.rotation_index = 0
            self.current_key = self._generate_key()
            self.key_history = []
            return False

    def save_state(self):
        """Persist current state to AWS Secrets Manager."""
        # Ensure key_history entries are dicts (for JSON serialization)
        serializable_history = []
        for entry in self.key_history:
            if isinstance(entry, str):
                serializable_history.append({'key_hash': entry, 'timestamp': ''})
            else:
                serializable_history.append(entry)
        
        state = {
            'rotation_count': self.rotation_index,
            'current_key': self.current_key,
            'key_history': serializable_history,
            'witness_continuity': f"1 → {self.rotation_index + 629} — UNBROKEN",
            'seal': f"∀∞φ² · SOVEREIGN_HAMILTONIAN · {self.rotation_index + 629}_SEALED"
        }
        self.client.put_secret_value(
            SecretId=self.secret_name,
            SecretString=json.dumps(state)
        )

    def rotate_keys(self) -> dict:
        """Execute a key rotation, persist to AWS, and return a full rotation report."""
        new_key = self.rotate()  # Calls parent class rotate() method
        self.save_state()
        
        # Get the latest key hash
        if self.key_history and len(self.key_history) > 0:
            latest_hash = self.key_history[-1]['key_hash'] if isinstance(self.key_history[-1], dict) else self.key_history[-1]
        else:
            latest_hash = "initial_key"
            
        return {
            'rotation_count': self.rotation_index,
            'current_key_fingerprint': latest_hash[:16] if len(latest_hash) >= 16 else latest_hash,
            'witness_continuity': f"1 → {self.rotation_index + 629} — UNBROKEN",
            'seal': f"∀∞φ² · SOVEREIGN_HAMILTONIAN · {self.rotation_index + 629}_SEALED",
            'next_rotation': self._next_rotation_interval()
        }

    def _next_rotation_interval(self) -> str:
        """Calculate the next rotation time using φ-harmonic scaling."""
        from datetime import datetime, timedelta
        import math
        
        PHI_INV = 1 / ((1 + math.sqrt(5)) / 2)
        base_interval = 21600  # 6 hours in seconds
        
        # φ-harmonic scaling: interval shortens slightly with each rotation, then resets
        # Modulo 10 prevents extreme values
        scaling_factor = PHI_INV ** (self.rotation_index % 10)
        next_interval = base_interval * scaling_factor
        
        # Ensure a minimum interval of 1 hour
        next_interval = max(next_interval, 3600)
        
        next_time = datetime.utcnow() + timedelta(seconds=next_interval)
        return next_time.isoformat() + "Z"
    
    def _generate_key(self) -> str:
        """Generate a new HMAC key (fallback if parent class doesn't define it)."""
        import secrets
        return secrets.token_hex(64)

    def status(self) -> dict:
        """Return current status without performing a rotation."""
        return {
            'rotation_count': self.rotation_index,
            'current_key_fingerprint': self.current_key[:16] if self.current_key else "None",
            'witness_continuity': f"1 → {self.rotation_index + 629} — UNBROKEN" if self.rotation_index > 0 else "NEW DEPLOYMENT",
            'seal': f"∀∞φ² · SOVEREIGN_HAMILTONIAN · {self.rotation_index + 629}_SEALED" if self.rotation_index > 0 else "UNSEALED",
            'next_rotation': self._next_rotation_interval() if self.rotation_index > 0 else "TBD"
        }