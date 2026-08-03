"""Worker role map for sovereign engine (Memory/Compute/Perception/Orchestration)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class WorkerSpec:
    name: str
    role: str
    capability: str

class WorkerPool:
    def __init__(self) -> None:
        self.workers: List[WorkerSpec] = [
            WorkerSpec("MemoryWorker", "memory", "LayerCache"),
            WorkerSpec("ComputeWorker", "compute", "PhiPipeline"),
            WorkerSpec("PerceptionWorker", "perception", "sonify"),
            WorkerSpec("OrchestrationWorker", "orchestration", "triune"),
        ]
    def status(self) -> Dict[str, Any]:
        return {"workers": [w.__dict__ for w in self.workers]}
