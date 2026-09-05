"""Logging configuration for fastMCP."""

import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for fastMCP."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

logger = logging.getLogger("fastMCP")
