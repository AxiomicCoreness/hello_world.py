"""Pydantic settings for the sovereign IRC bridge.

Cert paths are optional at import time so dual-gate collection stays clean.
Bridge connect paths call ``IRCSettings.require_mtls()`` and fail-fast when
certs are missing — no ghost-pass runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class IRCSettings(BaseSettings):
    host: str = Field(default="irc.abjects.net", description="Target IRC server")
    port: int = Field(
        default=6697,
        ge=1,
        le=65535,
        description="Target IRC port (6697 TLS/mTLS)",
    )
    mtls_cert_path: Optional[Path] = Field(
        default=None, description="Path to client certificate (.pem)"
    )
    mtls_key_path: Optional[Path] = Field(
        default=None, description="Path to client private key (.pem)"
    )
    mtls_ca_path: Optional[Path] = Field(
        default=None, description="Path to CA bundle for server verification"
    )

    model_config = SettingsConfigDict(env_prefix="IRC_", extra="ignore")

    @field_validator("mtls_cert_path", "mtls_key_path", "mtls_ca_path")
    @classmethod
    def validate_certs_exist_when_set(cls, v: Optional[Path]) -> Optional[Path]:
        if v is None:
            return v
        if not v.exists():
            raise ValueError(f"mTLS file not found: {v}")
        return v

    def require_mtls(self) -> tuple[Path, Path, Path]:
        """Fail-fast when mTLS material is absent (no ghost-pass connect)."""
        missing = [
            name
            for name, path in (
                ("mtls_cert_path", self.mtls_cert_path),
                ("mtls_key_path", self.mtls_key_path),
                ("mtls_ca_path", self.mtls_ca_path),
            )
            if path is None
        ]
        if missing:
            raise RuntimeError(
                "mTLS required for irc.abjects.net bridge connect; "
                f"unset: {', '.join(missing)} (mount secrets or set IRC__* paths)"
            )
        assert self.mtls_cert_path and self.mtls_key_path and self.mtls_ca_path
        for p in (self.mtls_cert_path, self.mtls_key_path, self.mtls_ca_path):
            if not p.exists():
                raise RuntimeError(f"mTLS file not found: {p}")
        return self.mtls_cert_path, self.mtls_key_path, self.mtls_ca_path


class BridgeSettings(BaseSettings):
    ws_bind_host: str = Field(default="0.0.0.0")
    ws_bind_port: int = Field(default=8080, ge=1024, le=65535)
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["https://axiomiccoreness.local"]
    )
    # Fixed typo from paste: max-s_buffer_size → max_buffer_size
    max_buffer_size: int = Field(
        default=65536, ge=1024, description="Max byte buffer per read"
    )

    model_config = SettingsConfigDict(env_file=".env", env_prefix="BRIDGE_", extra="ignore")


class DeploymentSettings(BaseSettings):
    environment: str = Field(
        default="production", pattern="^(development|staging|production)$"
    )
    log_level: str = Field(default="INFO")
    autonomous_mode: bool = Field(
        default=True, description="Enable automated K8s scaling/health"
    )

    model_config = SettingsConfigDict(env_prefix="DEPLOY_", extra="ignore")


class SovereignConfig(BaseSettings):
    """Master config aggregating all subsets."""

    irc: IRCSettings = Field(default_factory=IRCSettings)
    bridge: BridgeSettings = Field(default_factory=BridgeSettings)
    deploy: DeploymentSettings = Field(default_factory=DeploymentSettings)

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )

    @model_validator(mode="after")
    def _team_ports_ui_note(self) -> "SovereignConfig":
        # Team UI labels 6666-6669 live in TeaVM debug-oracle; bridge uses TLS 6697.
        return self


_settings: Optional[SovereignConfig] = None


def get_settings() -> SovereignConfig:
    """Lazy singleton — safe to import without certs present."""
    global _settings
    if _settings is None:
        _settings = SovereignConfig()
    return _settings
