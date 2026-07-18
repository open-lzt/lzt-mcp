"""e2e: round-trip against a running local lzt-eventus dev instance.

Not run live in this session — lzt-eventus needs Postgres/Redis per `EngineConfig`, unlike
`lzt-testnet`'s pure in-memory mode, so this test is structural (verified to import and wire
correctly) rather than exercised against a real server. Skipped by default like every other
`@pytest.mark.e2e` test in this suite.
"""

from __future__ import annotations

import os

import pytest

from lzt_dev_mcp.eventus.tools import get_event_types, list_subscriptions

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_eventus_round_trip() -> None:
    os.environ["LZT_DEV_MCP_LZT_EVENTUS_BASE_URL"] = "http://127.0.0.1:8001"
    event_types = await get_event_types()
    assert isinstance(event_types, list)

    subscriptions = await list_subscriptions()
    assert isinstance(subscriptions, list)
