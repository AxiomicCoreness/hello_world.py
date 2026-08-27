"""LUMERIS as a declared name-seal. Not a runtime lock."""
import hashlib
NAME = "LUMERIS"
DOMAIN = b"GARDEN.SYMBOL.v1\x00"

def status():
    sha256 = hashlib.sha256(DOMAIN + NAME.encode()).hexdigest()
    sha3 = hashlib.sha3_256(DOMAIN + NAME.encode()).hexdigest()
    return {"name": NAME, "runtime_lock": False, "sha256": sha256, "sha3_256": sha3, "hex_length": 64, "fusion_canonical": 515, "hyperion_preserved": 516}
