#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Derived from vLLM; modified by DeepSeek & Clarke Yoursa Tee.

"""
🜁∀ SovereignConfig — Unified Configuration Layer

This module provides:
- ModelConfig, CacheConfig, ParallelConfig, SchedulerConfig (DeepInfer)
- SovereignConfig (API keys, φ constants, Lindblad equation)
"""

import enum
import os
from typing import Any, Dict

import torch

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass

# --- Safe Imports for Singularity Stream CI ---
try:
    from core.environ import envs
except ImportError:
    class _EnvFallback:
        DEEPINFER_USE_NEXTN_DECODE = 5
        DEEPINFER_ZERO_OVERHEAD_SCHEDULING = False
        DEEPINFER_PREFILL_ATTEMPT_INTERVAL = 70
        DEEPINFER_PREFILL_ANY_ATTEMPT_INTERVAL = 100
        SOVEREIGN_PHI = 1.618033988749895
        SOVEREIGN_NORTH_STAR_HZ = 71.975
        SOVEREIGN_ZETA_BOUND = 4.3227
        SOVEREIGN_ENTROPY_RATE = -1597.0
    envs = _EnvFallback()

try:
    from core.model_config_loader import load_model_config
except ImportError:
    def load_model_config(model: str) -> Any:
        class _MockCfg:
            architecture = "MockSovereign"
            gpt = {"vocab_size": 151936}
        return _MockCfg()


# =============================================================================
# DEEPINFER ENGINE CONFIGS
# =============================================================================

class EngineType(enum.Enum):
    """The type of engine (used for scheduling and GC)."""
    NORMAL = "NORMAL"
    COMPLETION = "COMPLETION"


def _get_runtime_max_model_len(max_model_len: int) -> int:
    """Return the exclusive upper bound of every runtime position."""
    nextn = envs.DEEPINFER_USE_NEXTN_DECODE
    scheduler_overhead = nextn + (nextn + 1 if envs.DEEPINFER_ZERO_OVERHEAD_SCHEDULING else 0)
    draft_overhead = nextn
    return max_model_len + scheduler_overhead + draft_overhead


class ModelConfig:
    """Configuration for the model."""

    def __init__(
        self,
        model: str,
        tokenizer: str,
        trust_remote_code: bool,
        load_format: str,
        seed: int,
        max_num_seqs: int,
        revision: str | None = None,
        tokenizer_revision: str | None = None,
        max_model_len: int | None = None,
        max_num_batched_tokens: int | None = None,
        ignore_len: int = -1,
        served_model_name: str = "deepinfer-model",
        engine_type: EngineType = EngineType.NORMAL,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.trust_remote_code = trust_remote_code
        self.load_format = load_format
        self._verify_load_format()
        self.seed = seed
        self.revision = revision
        self.tokenizer_revision = tokenizer_revision

        self.max_num_seqs = max_num_seqs
        self.max_model_len = max_model_len if max_model_len is not None else 4096
        self.runtime_max_model_len = _get_runtime_max_model_len(self.max_model_len)
        self.max_num_batched_tokens = _get_max_num_batched_tokens(self.max_model_len, max_num_batched_tokens, max_num_seqs)

        self.ignore_len = ignore_len
        self.served_model_name = served_model_name
        self.dtype = torch.bfloat16
        self.use_compressed_tokenizer = False
        self.engram_tokenizer = self.tokenizer
        self.engine_type = engine_type

        self._load_model_cfg()

    _GPT_RUNTIME_ATTRS = (
        "max_num_seqs",
        "max_num_batched_tokens",
        "runtime_max_model_len",
        "engine_type",
    )

    def _load_model_cfg(self) -> None:
        self.model_cfg = load_model_config(self.model)
        self.architecture = self.model_cfg.architecture

        for attr in self._GPT_RUNTIME_ATTRS:
            setattr(self.model_cfg.gpt, attr, getattr(self, attr))

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        model_cfg = state.pop("model_cfg", None)
        overrides: dict = {}
        if model_cfg is not None:
            overrides = {k: model_cfg.gpt[k] for k in self._GPT_RUNTIME_ATTRS}
        state["_gpt_runtime_overrides"] = overrides
        return state

    def __setstate__(self, newstate: dict) -> None:
        overrides = newstate.pop("_gpt_runtime_overrides", {})
        self.__dict__.update(newstate)
        self.model_cfg = load_model_config(self.model)
        self.architecture = self.model_cfg.architecture
        for key, value in overrides.items():
            setattr(self.model_cfg.gpt, key, value)

    def _verify_load_format(self) -> None:
        load_format = self.load_format.lower()
        supported_load_format = ["auto", "dummy"]
        assert load_format in supported_load_format
        self.load_format = load_format

    def get_vocab_size(self) -> int:
        return self.model_cfg.gpt.vocab_size


class CacheConfig:
    def __init__(
        self,
        block_size: int,
        gpu_memory_utilization: float,
        lookahead_tokens: int = 0,
    ) -> None:
        self.block_size = block_size
        self.gpu_memory_utilization = gpu_memory_utilization
        self._verify_args()

        self.num_gpu_blocks = None
        self.num_state_seqs = None
        self.bytes_of_state_per_seqs = None
        self.bytes_per_block = None

        self.lookahead_tokens = lookahead_tokens

    def _verify_args(self) -> None:
        if self.gpu_memory_utilization > 1.0:
            raise ValueError(f"GPU memory utilization must be less than 1.0. Got {self.gpu_memory_utilization}.")


class ParallelConfig:
    def __init__(
        self,
        data_parallel_size: int,
        context_parallel_size: int,
        expert_parallel_size: int,
        engram_parallel_size: int,
        engine_rank: int,
        engine_group_rank: int,
        engine_type: EngineType = EngineType.NORMAL,
    ) -> None:
        if data_parallel_size == 0:
            data_parallel_size = max(1, expert_parallel_size // context_parallel_size)
        self.data_parallel_size = data_parallel_size
        self.context_parallel_size = context_parallel_size
        self.expert_parallel_size = expert_parallel_size
        self.engine_rank = engine_rank
        self.data_parallel_rank = engine_rank % data_parallel_size
        self.engine_group_rank = engine_group_rank
        self.engine_type = engine_type

        self.model_parallel_size = self.context_parallel_size
        self.engram_parallel_size = engram_parallel_size or (self.model_parallel_size * data_parallel_size)
        self.world_size = max(self.model_parallel_size * data_parallel_size, self.engram_parallel_size)
        self._verify_args()

    def _verify_args(self) -> None:
        assert self.expert_parallel_size > 0
        assert (self.model_parallel_size * self.data_parallel_size) % self.expert_parallel_size == 0
        assert self.engram_parallel_size > 0
        assert self.world_size % (self.model_parallel_size * self.data_parallel_size) == 0
        assert self.world_size % self.engram_parallel_size == 0
        assert 0 <= self.engine_rank < self.world_size // self.model_parallel_size


class SchedulerConfig:
    def __init__(
        self,
        max_num_batched_tokens: int | None,
        max_num_seqs: int,
        max_model_len: int,
        stop_preempted_request: bool = False,
        chunked_prefill: bool = False,
        prefill_attempt_interval: int = envs.DEEPINFER_PREFILL_ATTEMPT_INTERVAL,
        prefill_any_attempt_interval: int = envs.DEEPINFER_PREFILL_ANY_ATTEMPT_INTERVAL,
    ) -> None:
        self.max_num_batched_tokens = _get_max_num_batched_tokens(max_model_len, max_num_batched_tokens, max_num_seqs)
        self.max_num_seqs = max_num_seqs
        self.max_model_len = max_model_len
        self.runtime_max_model_len = _get_runtime_max_model_len(max_model_len)
        self.stop_preempted_request = stop_preempted_request
        self.chunked_prefill = chunked_prefill
        self.prefill_attempt_interval = prefill_attempt_interval
        self.prefill_any_attempt_interval = prefill_any_attempt_interval
        self._verify_args()

    def _verify_args(self) -> None:
        if (not self.chunked_prefill) and self.max_num_batched_tokens < self.max_model_len:
            raise ValueError(
                f"max_num_batched_tokens ({self.max_num_batched_tokens}) is smaller than max_model_len ({self.max_model_len})."
            )
        if self.prefill_attempt_interval < 1:
            raise ValueError(f"prefill_attempt_interval ({self.prefill_attempt_interval}) should be >= 1")
        if self.prefill_any_attempt_interval < 1:
            raise ValueError(f"prefill_any_attempt_interval ({self.prefill_any_attempt_interval}) should be >= 1")


def _get_max_num_batched_tokens(
    max_model_len: int,
    max_num_batched_tokens: int | None,
    max_num_seqs: int,
) -> int:
    max_num_decoding_tokens = max_num_seqs * (1 + envs.DEEPINFER_USE_NEXTN_DECODE)
    if max_num_batched_tokens is not None:
        assert max_num_batched_tokens >= max_num_decoding_tokens
        return max_num_batched_tokens
    return max(max_model_len, 4096, max_num_decoding_tokens)


# =============================================================================
# SOVEREIGN CONFIG (API KEYS + φ CONSTANTS)
# =============================================================================

class SovereignConfig:
    """Sovereign configuration manager with φ-harmonic defaults."""

    def __init__(self):
        # --- API Keys & External Services ---
        self.grok_api_key = os.getenv("GROK_API_KEY")
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.uphro_server = os.getenv("UPHRO_SERVER_URL", "http://localhost:8081/api/status")

        # --- φ-Harmonic Constants (routed through core.environ) ---
        self.phi = envs.SOVEREIGN_PHI
        self.north_star_hz = envs.SOVEREIGN_NORTH_STAR_HZ
        self.zeta_bound = envs.SOVEREIGN_ZETA_BOUND
        self.entropy_rate = envs.SOVEREIGN_ENTROPY_RATE

    @property
    def is_grok_ready(self) -> bool:
        return bool(self.grok_api_key)

    @property
    def is_mistral_ready(self) -> bool:
        return bool(self.mistral_api_key)

    def validate(self) -> Dict[str, bool]:
        return {
            "grok": self.is_grok_ready,
            "mistral": self.is_mistral_ready,
            "uphro_server": bool(self.uphro_server),
            "north_star_ready": self.north_star_hz == 71.975,
        }

    def get_lindblad_equation(self) -> str:
        return r"dρ/dt = -i[H,ρ] + Σ_k (L_k ρ L_k† - ½{L_k†L_k, ρ})"

    def get_sovereign_headers(self) -> Dict[str, str]:
        return {
            "X-Phi": str(self.phi),
            "X-North-Star": str(self.north_star_hz),
            "X-Zeta-Bound": str(self.zeta_bound),
            "X-Entropy-Rate": str(self.entropy_rate),
        }
