"""Gearbox service."""

from fastMCP.constants import PHI

class GearboxService:
    def __init__(self):
        self.phi = PHI
        self.state = "idle"

    def engage(self):
        self.state = "engaged"
        return {"state": "engaged", "phi": self.phi}
