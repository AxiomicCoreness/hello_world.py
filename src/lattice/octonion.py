"""Re-export octonion surfaces — no rewrite."""
try:
    from octonion_self_healer import *  # noqa: F401,F403
except Exception:
    pass
try:
    from octonion_table import *  # noqa: F401,F403
except Exception:
    pass
