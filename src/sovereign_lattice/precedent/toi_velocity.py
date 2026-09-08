"""TOI‑Velocity exact collision timing."""

from dataclasses import dataclass
from typing import Tuple

PHI_INV = 1 / PHI

@dataclass
class TOIState:
    position: float
    velocity: float
    time: float

@dataclass
class TOIResult:
    time_of_impact: float
    post_velocity: float
    pre_velocity: float
    gradient_correction: float

def compute_toi(s1: TOIState, s2: TOIState) -> TOIResult:
    dx = s2.position - s1.position
    dv = s2.velocity - s1.velocity
    if abs(dv) < 1e-12:
        t_impact = 1e12
    else:
        t_impact = -dx / dv
    v_post_1 = s1.velocity + dv * PHI_INV
    v_post_2 = s2.velocity - dv * PHI_INV
    gradient_correction = PHI ** (-709)   # ultra‑stillness
    return TOIResult(t_impact, v_post_1, s1.velocity, gradient_correction)
