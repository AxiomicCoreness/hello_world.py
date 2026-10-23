"""Pydantic settings for the sovereign IRC bridge.

mTLS paths are **required**. Missing ``IRC__MTLS_*`` (or nonexistent PEM files)
raises ``pydantic.ValidationError`` at config load — FastAPI lifespan calls
``get_settings()`` so the app does not serve without certs (no ghost-pass).
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
    mtls_cert_path: Path = Field(..., description="Path to client certificate (.pem)")
    mtls_key_path: Path = Field(..., description="Path to client private key (.pem)")
    mtls_ca_path: Path = Field(..., description="Path to CA bundle for server verification")

    model_config = SettingsConfigDict(env_prefix="IRC_", extra="ignore")

    @field_validator("mtls_cert_path", "mtls_key_path", "mtls_ca_path")
    @classmethod
    def validate_certs_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"mTLS file not found: {v}")
        if not v.is_file():
            raise ValueError(f"mTLS path is not a file: {v}")
        return v

    def require_mtls(self) -> tuple[Path, Path, Path]:
        """Return cert material (already validated at model construction)."""
        return self.mtls_cert_path, self.mtls_key_path, self.mtls_ca_path


class BridgeSettings(BaseSettings):
    ws_bind_host: str = Field(default="0.0.0.0")
    ws_bind_port: int = Field(default=8080, ge=1024, le=65535)
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["https://axiomiccoreness.local"]
    )
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
    def _mtls_material_present(self) -> "SovereignConfig":
        # Nested IRCSettings already required paths + existence; re-touch for clarity.
        self.irc.require_mtls()
        return self


_settings: Optional[SovereignConfig] = None


def get_settings() -> SovereignConfig:
    """Lazy singleton — raises ValidationError if mTLS env/files are missing."""
    global _settings
    if _settings is None:
        _settings = SovereignConfig()
    return _settings


def reset_settings() -> None:
    """Test helper."""
    global _settings
    _settings = None
