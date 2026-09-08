"""Lagrangian dynamics for legged robots."""

import numpy as np
from dataclasses import dataclass
from typing import List

@dataclass
class LagrangianDynamics:
    mass_matrix: np.ndarray              # M(q)
    nonlinear_forces: np.ndarray          # n(q, q̇)
    control_torques: np.ndarray           # τ
    contact_jacobians: List[np.ndarray]   # C_i(q)
    contact_forces: List[np.ndarray]      # f_i

    def compute_acceleration(self) -> np.ndarray:
        total_force = self.control_torques.copy()
        for C, f in zip(self.contact_jacobians, self.contact_forces):
            total_force += C @ f
        total_force -= self.nonlinear_forces
        try:
            return np.linalg.solve(self.mass_matrix, total_force)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(self.mass_matrix) @ total_force

    def in_flight(self) -> bool:
        return len(self.contact_forces) == 0
