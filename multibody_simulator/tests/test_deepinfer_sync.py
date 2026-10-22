# tests/test_deepinfer_sync.py
from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable, Generator

import pytest
import torch

# Prevent CI failure if deepinfer isn't installed in the base environment
deepinfer = pytest.importorskip("deepinfer")
from deepinfer.utils import _sync_debug_arbiter, allow_cuda_sync, forbid_cuda_sync

# ... [Paste your exact test file content here, keeping all the threading tests] ...
