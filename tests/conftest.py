"""Shared fixtures: FastMCP in-process test client + a clean-env autouse fixture."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from fastmcp import Client

from lzt_dev_mcp.server import build_app


@pytest.fixture(autouse=True)
def _clean_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test starts with no lzt-dev-mcp env vars leaking from the shell."""
    for key in list(__import__("os").environ):
        if key.startswith("LZT_DEV_MCP_"):
            monkeypatch.delenv(key, raising=False)


@pytest_asyncio.fixture
async def mcp_client() -> AsyncIterator[Client[Any]]:
    app = build_app()
    async with Client(app) as client:
        yield client
