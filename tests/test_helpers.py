"""Unit: get_rate_limits/get_error_catalog; e2e-marked get_testnet_status reachability."""

from __future__ import annotations

import pytest

from lzt_dev_mcp.helpers.tools import get_error_catalog, get_rate_limits, get_testnet_status


@pytest.mark.asyncio
async def test_get_rate_limits_has_known_classes() -> None:
    limits = {entry.rate_class: entry.requests_per_minute for entry in await get_rate_limits()}
    assert limits["general"] == 120
    assert limits["search"] == 20
    assert limits["forum"] == 300


@pytest.mark.asyncio
async def test_get_error_catalog_delegates_to_catalog_module() -> None:
    entries = await get_error_catalog()
    names = {entry.name for entry in entries}
    assert "RateLimited" in names
    assert "AuthFailed" in names


@pytest.mark.asyncio
async def test_get_testnet_status_unreachable_when_unconfigured() -> None:
    status = await get_testnet_status()
    assert status.reachable is False
    assert status.latency_ms is None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_testnet_status_reachable_against_live_instance() -> None:
    import os

    os.environ["LZT_DEV_MCP_TESTNET_BASE_URL"] = "http://127.0.0.1:8765"
    status = await get_testnet_status()
    assert status.reachable is True
