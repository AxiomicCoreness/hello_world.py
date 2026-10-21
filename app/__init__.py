from __future__ import annotations

import importlib.util
import sys
from pathlib import Path as _Path
from types import ModuleType

__version__ = "5.0.0"
ZETA_BOUND = 2.366
ZETA_RAW_PRODUCT = 4.322935
GOLDEN_GATE = "phi**2 - phi - 1 == 0"

__all__ = [
    "__version__",
    "ZETA_BOUND",
    "ZETA_RAW_PRODUCT",
    "GOLDEN_GATE",
    "app_main",
]

# ``uvicorn app:app_main`` resolves ``app`` to this package, not to the
# repo-root ``app.py`` (a package shadows a same-named module). Re-export
# ``app_main`` from ``app.py`` lazily so the documented target keeps working
# and ``import app.config`` does not pull in garden_surgery.
_ROOT_APP_PY = _Path(__file__).resolve().parents[1] / "app.py"
_ROOT_APP_MODULE = "_garden_root_app_py"


def _load_root_app_py() -> ModuleType:
    """Dynamically load the repo-root app.py as a distinct module."""
    
    # If Uvicorn is running with --reload, we need to force a re-read
    # if the file has changed.
    if _ROOT_APP_MODULE in sys.modules:
        mod = sys.modules[_ROOT_APP_MODULE]
        # Check if the file has been modified since it was loaded
        if hasattr(mod, "__file__") and mod.__file__ is not None:
            mod_path = _Path(mod.__file__)
            if mod_path.exists() and mod_path.stat().st_mtime <= _Path(_ROOT_APP_PY).stat().st_mtime:
                return mod
        # If file is gone or older, drop the cache and reload
        sys.modules.pop(_ROOT_APP_MODULE, None)

    spec = importlib.util.spec_from_file_location(_ROOT_APP_MODULE, _ROOT_APP_PY)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {_ROOT_APP_PY}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[_ROOT_APP_MODULE] = mod
    
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(_ROOT_APP_MODULE, None)
        raise
        
    return mod


def __getattr__(name: str):
    """Lazy-load the root app.py only when `app_main` is explicitly requested."""
    if name == "app_main":
        if not _ROOT_APP_PY.is_file():
            raise AttributeError(
                f"module 'app' has no attribute 'app_main' ({_ROOT_APP_PY} missing)"
            )
        
        try:
            root_mod = _load_root_app_py()
            value = getattr(root_mod, "app_main", None)
            
            if value is None:
                # app.py sets app_main = None when garden_surgery fails to import.
                raise AttributeError(
                    "app_main is None: app.py could not import garden_surgery"
                )
            return value
            
        except Exception as e:
            raise AttributeError(f"Failed to load app_main from root app.py: {e}")
            
    raise AttributeError(f"module 'app' has no attribute {name!r}")
