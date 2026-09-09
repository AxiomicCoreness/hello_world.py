"""Custom exceptions for fastMCP."""

class FastMCPError(Exception):
    """Base exception for fastMCP."""
    pass

class BindError(FastMCPError):
    """Bind policy violation."""
    pass

class FillError(FastMCPError):
    """FILLED invariant violation."""
    pass
