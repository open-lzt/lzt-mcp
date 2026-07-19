"""`send_request(target="testnet")` round-trips a real lzt-testnet server.

Boots the `lzt_testnet` app in a background uvicorn thread and checks that both a market-scoped
method (`GetLot`) and a forum-scoped method (`CategoriesGet`) return 200 against the mock. A 401 on
the forum call means the request reached the real prod-api.lolz.live — i.e. `forum_base_url` was
not overridden onto the testnet host.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import httpx
import pytest
import uvicorn
from lzt_testnet.api.app import create_app

from lzt_dev_mcp.config import Settings
from lzt_dev_mcp.testing import tools as testing_tools

_STARTUP_TIMEOUT_S = 5.0
_POLL_S = 0.05


@pytest.fixture
def testnet_base_url() -> Iterator[str]:
    config = uvicorn.Config(create_app(), host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + _STARTUP_TIMEOUT_S
    while not server.started:
        if time.monotonic() > deadline:
            server.should_exit = True
            thread.join(timeout=1.0)
            raise RuntimeError("testnet server did not start")
        time.sleep(_POLL_S)

    port = server.servers[0].sockets[0].getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    with httpx.Client(timeout=_STARTUP_TIMEOUT_S) as probe:
        while probe.get(f"{base_url}/testnet/health").status_code != 200:
            time.sleep(_POLL_S)

    yield base_url

    server.should_exit = True
    thread.join(timeout=5.0)


@pytest.fixture
def _testnet_settings(testnet_base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point mcp's Settings at the live testnet for the duration of the test."""
    monkeypatch.setenv("LZT_DEV_MCP_TESTNET_BASE_URL", testnet_base_url)
    # send_request builds Settings() itself; the env var above is what it reads.
    assert Settings().testnet_base_url == testnet_base_url


@pytest.mark.asyncio
@pytest.mark.usefixtures("_testnet_settings")
async def test_market_method_round_trips_testnet() -> None:
    result = await testing_tools.send_request(
        method_name="GetLot", params={"item_id": 123}, target="testnet"
    )
    assert result.status == 200


@pytest.mark.asyncio
@pytest.mark.usefixtures("_testnet_settings")
async def test_forum_method_does_not_leak_to_prod() -> None:
    """A forum-scoped method must hit the local testnet (200), not real prod-api.lolz.live (401)."""
    result = await testing_tools.send_request(
        method_name="CategoriesGet", params={"category_id": 1}, target="testnet"
    )
    assert result.status == 200
