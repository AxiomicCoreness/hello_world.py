"""Re-export E8 surfaces — no rewrite of sources."""
try:
    from lattice.e8_symplectic import *  # noqa: F401,F403
except Exception:
    pass
try:
    from quantum.e8_cartan import *  # noqa: F401,F403
except Exception:
    pass
