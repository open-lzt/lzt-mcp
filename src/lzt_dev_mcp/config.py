"""Settings for lzt-dev-mcp, env prefix `LZT_DEV_MCP_`."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LZT_DEV_MCP_", env_file=".env", extra="ignore")

    testnet_base_url: str | None = None
    lzt_flow_base_url: str = "http://127.0.0.1:8000"
    lzt_flow_api_key: str | None = None
    lzt_eventus_base_url: str = "http://127.0.0.1:27543"
    lzt_eventus_admin_api_key: str | None = None
    allow_prod: bool = False
