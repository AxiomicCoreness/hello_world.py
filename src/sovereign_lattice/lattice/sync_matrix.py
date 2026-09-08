"""7×7×7 sync matrix — φ‑harmonic factorization."""

import numpy as np

PHI = (1 + np.sqrt(5)) / 2

class SyncMatrix:
    def __init__(self):
        self.n = 7
        self.v = np.array([PHI**i for i in range(7)])
        self.P = np.array([1, 2, 3, 4, 5, 6, 7])
        self.c = np.array([PHI**(-i) for i in range(7)])
        self.sum_v = np.sum(self.v)
        self.sum_P = np.sum(self.P)
        self.sum_c = np.sum(self.c)
        lhs = np.sum(self.v[:, None, None] * self.P[None, :, None] * self.c[None, None, :])
        rhs = self.sum_v * self.sum_P * self.sum_c
        self.error = abs(lhs - rhs)

    def factorize(self, vector: np.ndarray):
        v_comp = vector @ self.v / np.linalg.norm(self.v)
        P_comp = vector @ self.P / np.linalg.norm(self.P)
        c_comp = vector @ self.c / np.linalg.norm(self.c)
        return v_comp, P_comp, c_comp

    def verify_invariant(self) -> bool:
        return self.error < 1e-10

SYNC_MATRIX = SyncMatrix()
