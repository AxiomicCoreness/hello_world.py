import json
from collections import defaultdict
from datetime import datetime, timezone
import math

PHI = (1 + math.sqrt(5)) / 2

class OctonionAnomalyStore:
    def __init__(self, max_entries=100):
        self.entries = []
        self.max_entries = max_entries
        self.hot_pairs = defaultdict(float)  # pair → φ‑weighted score

    def log(self, pair, context):
        timestamp = datetime.now(timezone.utc).isoformat()
        self.entries.append({"pair": pair, "timestamp": timestamp, "context": context})
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)
        # Update hot pairs with φ‑weighted recency
        for stored in self.entries:
            age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(stored["timestamp"])).total_seconds() / 3600
            weight = math.exp(-age_hours / PHI)  # φ‑decay
            self.hot_pairs[stored["pair"]] += weight

    def get_hot_pairs(self, threshold=0.5):
        return [pair for pair, score in self.hot_pairs.items() if score > threshold]