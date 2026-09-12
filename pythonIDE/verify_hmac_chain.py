#!/usr/bin/env python3
"""
pythonIDE/verify_hmac_chain.py — read-only HMAC chain verifier.
Ledger policy: NO_LEDGER_WRITE. Precedent: 8206.
"""

from __future__ import annotations

try:
    # Package form
    from pythonIDE.attenuation_learning import (
        REPO_URL,
        DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY,
        PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
        AttenuationLearningConcat,
    )
    HMAC_KEY = AttenuationLearningConcat.HMAC_KEY
except ImportError:
    # Script form
    from attenuation_learning import (
        REPO_URL,
        DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY,
        PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
        AttenuationLearningConcat,
    )
    HMAC_KEY = AttenuationLearningConcat.HMAC_KEY

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_CHAIN = "ledger/attenuation_chain.jsonl"
