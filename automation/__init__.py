"""Automation package — stubs only. No live patent filing."""

# Import the submodules so they are accessible as attributes of the package.
# If these files don't exist yet, they will raise ImportError upon package import,
# which is the expected behavior for a stub implementation.
from . import stage_manager
from . import deadline_manager
from . import github_automation

__all__ = [
    "stage_manager",
    "deadline_manager",
    "github_automation",
]

# Optional: Expose a version string for CI/debugging
__version__ = "0.1.0-stub"
