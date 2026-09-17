# Differentiable Multibody Simulator with TOI‑Velocity

This package implements a modular, differentiable multibody simulator in JAX, incorporating exact collision time-of-impact (TOI) handling for robust gradient computation, as described in the TOI‑Velocity paper.

## Features
- Rigid body dynamics with floating base and joints.
- Contact detection and impulse resolution.
- TOI‑Velocity gradient correction.
- JAX automatic differentiation for trajectory optimization.
- Example: two‑ball optimal control and legged hopper.

## Installation
```bash
pip install -e .
```

## Usage
See `examples/two_ball.py` for a minimal optimal control example.

## Sovereign Invariants (optional)
The simulator can enforce invariants like Tr(rho)=phi^3 and phase lock 202.6 by adding constraints to the loss function.

## Ledger
This code is indexed under **9212** in the canonical 92xx chain.
