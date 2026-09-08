"""Thin hopper optimizer + re-export of step_hopper."""
from multibody_simulator.hopper_toi import step_hopper, G, E
import jax.numpy as jnp
import jax


def main():
    s0 = jnp.array([1.0, 0.0])
    dt = 0.01
    u = jnp.full((80,), 9.81)

    def loss(u_seq):
        s = s0
        for ui in u_seq:
            s, *_ = step_hopper(s, ui, dt)
        return (s[0] - 2.0) ** 2 + s[1] ** 2

    g = jax.grad(loss)(u)
    print("hopper grad norm", float(jnp.linalg.norm(g)))
    print("final loss", float(loss(u)))


if __name__ == "__main__":
    main()
