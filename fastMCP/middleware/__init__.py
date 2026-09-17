"""Middleware package for fastMCP."""

from fastMCP.middleware.cors import cors_middleware
from fastMCP.middleware.auth import auth_middleware
from fastMCP.middleware.metrics import metrics_middleware
