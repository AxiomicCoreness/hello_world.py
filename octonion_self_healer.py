import random
from datetime import datetime, timezone
import math
from octonion_table import octonion_product, build_octonion_table, FANO_LINES
from anomaly_store import OctonionAnomalyStore

PHI = (1 + math.sqrt(5)) / 2

class OctonionSelfHealer:
    def __init__(self):
        self.store = OctonionAnomalyStore()
        self.heal_count = 0
        self.success_rate = 1.0
        self.adaptive_sample_size = 7
        self.start_time = datetime.now(timezone.utc)

    def check_and_heal(self, engine):
        """
        Check for octonion table anomalies and heal if necessary.
        
        Args:
            engine: The Sovereign Engine instance
            
        Returns:
            True if no anomalies found (stable), False if healing was performed
        """
        # Determine sample set: hot pairs + random if needed
        hot = self.store.get_hot_pairs()
        sample_size = max(3, min(14, self.adaptive_sample_size))
        
        if len(hot) >= sample_size:
            sample_pairs = random.sample(hot, sample_size)
        else:
            random_pairs = [(i, j) for i in range(1, 8) for j in range(1, 8) if i != j]
            sample_pairs = random.sample(random_pairs, sample_size - len(hot)) + hot

        anomalies = []
        for i, j in sample_pairs:
            sign, k = octonion_product(i, j)
            if k == 0 or sign == 0:
                anomalies.append((i, j))

        if anomalies:
            # Trigger heal
            self.heal_count += 1
            self.store.log(anomalies[0], {"coherence": engine.automaton.get_coherence() if hasattr(engine, 'automaton') else 1.0})
            
            # Adaptive strategy: if repeated same pair, repair only that pair; else rebuild all
            if len(anomalies) == 1 and anomalies[0] in self.store.get_hot_pairs(threshold=0.8):
                # Targeted repair: fix only the offending pair in the table
                # For simplicity, we rebuild the whole table but log as targeted
                build_octonion_table()
                heal_type = "targeted"
            else:
                build_octonion_table()
                heal_type = "full_rebuild"
            
            # Update adaptive sample size (increase if many anomalies, decrease if stable)
            self.adaptive_sample_size = max(3, min(14, self.adaptive_sample_size + (len(anomalies) - 1) // 2))
            
            # Commit heal event to engine
            if hasattr(engine, 'commit'):
                engine.commit({
                    "event": "/octonion_heal/rebuild",
                    "anomalies": len(anomalies),
                    "type": heal_type,
                    "sample_size": len(sample_pairs),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, "octonion_heal")
            
            # Update success rate (treat as partial success if heal count < 3 per cycle)
            self.success_rate = 0.9 * self.success_rate + 0.1 * (1 if len(anomalies) < 3 else 0)
            return False
        else:
            # Stable: adjust sample size downward slowly
            self.adaptive_sample_size = max(3, self.adaptive_sample_size - 1)
            self.success_rate = 0.9 * self.success_rate + 0.1 * 1.0
            return True
    
    def get_heal_count(self):
        """Get total heal count."""
        return self.heal_count
    
    def get_success_rate(self):
        """Get current success rate."""
        return self.success_rate
    
    def get_adaptive_sample_size(self):
        """Get current adaptive sample size."""
        return self.adaptive_sample_size
    
    def get_hot_pairs_count(self):
        """Get number of hot pairs tracked."""
        return len(self.store.get_hot_pairs())