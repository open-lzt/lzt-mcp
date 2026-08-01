"""D-4 prod-guard: build_client's 4 required cases, per 00-decisions.md."""

from __future__ import annotations

import pytest
from pylzt.config import ClientConfig

from lzt_dev_mcp.config import Settings
from lzt_dev_mcp.errors import ProdBlocked, TestnetUnavailable
from lzt_dev_mcp.testing.client_factory import build_client


def test_prod_without_token_is_blocked() -> None:
    settings = Settings()
    with pytest.raises(ProdBlocked):
        build_client("prod", None, settings)


def test_prod_with_empty_token_is_blocked() -> None:
    settings = Settings()
    with pytest.raises(ProdBlocked):
        build_client("prod", "", settings)


def test_testnet_without_configured_url_is_unavailable() -> None:
    settings = Settings(testnet_base_url=None)
    with pytest.raises(TestnetUnavailable):
        build_client("testnet", None, settings)


def test_prod_with_real_token_keeps_the_real_hosts() -> None:
    settings = Settings()
    client = build_client("prod", "realtoken", settings)
    default = ClientConfig()
    assert client.config.base_url == default.base_url
    assert client.config.forum_base_url == default.forum_base_url


def test_testnet_with_configured_url_overrides_both_hosts() -> None:
    """Both hosts, not just `base_url` — a forum-scoped method with only the market host
    overridden goes to the real prod forum and comes back 401, which reads as a testnet bug."""
    settings = Settings(testnet_base_url="http://127.0.0.1:9000")
    client = build_client("testnet", None, settings)
    assert client.config.base_url == "http://127.0.0.1:9000"
    assert client.config.forum_base_url == "http://127.0.0.1:9000"
