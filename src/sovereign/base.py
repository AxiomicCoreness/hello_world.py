"""Base surface for the production layout.
Bridges the sovereign PlanckEngine to the vendored DeepInfer GPU worker.
"""

# Import the actual DeepInfer worker from the vendored submodule
# This assumes 'vendor/DeepEP' or the root repo has deepinfer available in PYTHONPATH
try:
    from deepinfer.worker.worker import WorkerBase as DeepInferWorkerBase
    from deepinfer.config import CacheConfig, ModelConfig, ParallelConfig, SchedulerConfig
    from deepinfer.engine.engine_type import EngineType
except ImportError:
    # Fallback for CI or local environments without the heavy GPU deps
    DeepInferWorkerBase = object

from sovereign.planck_engine_v2 import PlanckEngine

class SovereignBase(DeepInferWorkerBase):
    """Minimal base marker combining Sovereign math with DeepInfer GPU resources."""
    
    name = "SovereignBase"

    def __init__(self, *args, **kwargs):
        # Initialize the DeepInfer worker (if available)
        if DeepInferWorkerBase is not object:
            super().__init__(*args, **kwargs)
            
        # Initialize the Planck Engine constants for this worker
        self.engine_results = PlanckEngine.run()

    def get_zeta_bound(self) -> float:
        """Expose the canonical math to the DeepInfer loop."""
        return self.engine_results["zetaBound"]
