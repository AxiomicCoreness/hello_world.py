#!/usr/bin/env python3
"""Differentiable two-ball time-of-impact step."""
from __future__ import annotations

from typing import Any

import torch

RADIUS = 0.2
DIAMETER_SQUARED = (2.0 * RADIUS) ** 2
EPSILON = 1e-12


def split_state(state: torch.Tensor):
    return state[..., 0:2], state[..., 2:4], state[..., 4:6], state[..., 6:8]


def pack_state(position_one, position_two, velocity_one, velocity_two):
    return torch.cat([position_one, position_two, velocity_one, velocity_two], dim=-1)


def integrate_free(position_one, position_two, velocity_one, velocity_two, control, duration):
    position_one_next = position_one + velocity_one * duration + 0.5 * control * duration * duration
    position_two_next = position_two + velocity_two * duration
    velocity_one_next = velocity_one + control * duration
    return position_one_next, position_two_next, velocity_one_next, velocity_two


def time_of_impact(position_one, position_two, velocity_one, velocity_two, duration):
    relative_position = position_two - position_one
    relative_velocity = velocity_two - velocity_one
    quadratic_a = (relative_velocity * relative_velocity).sum(-1)
    quadratic_b = (2.0 * relative_position * relative_velocity).sum(-1)
    quadratic_c = (relative_position * relative_position).sum(-1) - DIAMETER_SQUARED
    discriminant = quadratic_b * quadratic_b - 4.0 * quadratic_a * quadratic_c
    root = torch.sqrt(torch.clamp(discriminant, min=0.0) + EPSILON)
    impact_time = (-quadratic_b - root) / (2.0 * quadratic_a + EPSILON)
    approaching = (relative_position * relative_velocity).sum(-1) < -EPSILON
    hit = approaching & (discriminant > EPSILON) & (impact_time > EPSILON) & (impact_time <= duration)
    return torch.where(hit, impact_time, torch.ones_like(impact_time) * duration), hit


def elastic_collision(position_one, position_two, velocity_one, velocity_two):
    normal = position_two - position_one
    normal = normal / torch.linalg.vector_norm(normal, dim=-1, keepdim=True).clamp_min(EPSILON)
    impulse = ((velocity_one - velocity_two) * normal).sum(-1, keepdim=True)
    return velocity_one - impulse * normal, velocity_two + impulse * normal


def step_with_toi(state: torch.Tensor, control: torch.Tensor, duration: float, radius: float = RADIUS):
    del radius
    state = torch.as_tensor(state, dtype=torch.float64)
    control = torch.as_tensor(control, dtype=state.dtype, device=state.device)
    position_one, position_two, velocity_one, velocity_two = split_state(state)
    impact_time, hit = time_of_impact(position_one, position_two, velocity_one, velocity_two, duration)

    p1, p2, v1, v2 = integrate_free(position_one, position_two, velocity_one, velocity_two, control, impact_time)
    post_v1, post_v2 = elastic_collision(p1, p2, v1, v2)
    remaining = (duration - impact_time).clamp_min(0.0)
    hit_state = pack_state(*integrate_free(p1, p2, post_v1, post_v2, control, remaining))
    free_state = pack_state(*integrate_free(position_one, position_two, velocity_one, velocity_two, control, duration))
    mask = hit.to(dtype=state.dtype).unsqueeze(-1)
    next_state = mask * hit_state + (1.0 - mask) * free_state
    event: dict[str, Any] = {"gamma": impact_time, "hit": hit, "dt": duration}
    return next_state, event