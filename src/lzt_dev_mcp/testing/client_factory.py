"""Builds an `pylzt.Client` targeting either testnet (default, safe) or prod (guarded).

D-4 (safety-critical, 00-decisions.md): `target="prod"` with no/empty token always raises
`ProdBlocked` — no env-var fallback, ever. `target="testnet"` with no configured
`testnet_base_url` always raises `TestnetUnavailable` — never silently falls through to prod.
"""

from __future__ import annotations

from typing import Literal

from pylzt import Client
from pylzt.config import ClientConfig

from lzt_dev_mcp.config import Settings
from lzt_dev_mcp.errors import ProdBlocked, TestnetUnavailable

__all__ = ["build_client"]

# Not a credential — this Client only builds requests against a locally-configured testnet
# host; no real token pool/auth is ever exercised with it.
_TESTNET_FAKE_TOKEN = "testnet-fake-token"


def build_client(
    target: Literal["testnet", "prod"], token: str | None, settings: Settings
) -> Client:
    if target == "prod":
        if not token:
            raise ProdBlocked()
        return Client([token])

    if not settings.testnet_base_url:
        raise TestnetUnavailable()
    # Override BOTH the market and forum hosts — otherwise forum-scoped methods (e.g. category
    # listings) leak to the real prod-api.lolz.live and return a real 401 instead of hitting the
    # testnet. The mock serves both surfaces on the one base URL.
    return Client(
        [_TESTNET_FAKE_TOKEN],
        config=ClientConfig(
            base_url=settings.testnet_base_url,
            forum_base_url=settings.testnet_base_url,
        ),
    )
