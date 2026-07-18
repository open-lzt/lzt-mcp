"""D-4 prod-guard: build_client's 4 required cases, per 00-decisions.md."""

from __future__ import annotations

import pytest

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


def test_prod_with_real_token_returns_client_with_no_base_url_override() -> None:
    settings = Settings()
    client = build_client("prod", "realtoken", settings)
    assert client is not None


def test_testnet_with_configured_url_returns_client() -> None:
    settings = Settings(testnet_base_url="http://127.0.0.1:9000")
    client = build_client("testnet", None, settings)
    assert client is not None
