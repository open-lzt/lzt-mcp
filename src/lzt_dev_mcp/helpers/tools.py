"""Group C MCP tools: rate limits, error catalog, testnet reachability.

Plain undecorated `async def` functions per D-9.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from pylzt.types import RateClass

from lzt_dev_mcp.catalog.errors_catalog import ErrorCatalogEntry, collect_error_classes
from lzt_dev_mcp.config import Settings

__all__ = [
    "RateLimitInfo",
    "TestnetStatus",
    "get_error_catalog",
    "get_rate_limits",
    "get_testnet_status",
]

# Official published ceilings (pylzt.config.ClientConfig docstring, confirmed 2026-07-04).
_RATE_LIMITS: dict[RateClass, int] = {
    RateClass.GENERAL: 120,
    RateClass.SEARCH: 20,
    RateClass.FORUM: 300,
    RateClass.ANTIPUBLIC: 60,
}


@dataclass(frozen=True)
class RateLimitInfo:
    rate_class: str
    requests_per_minute: int


@dataclass(frozen=True)
class TestnetStatus:
    reachable: bool
    latency_ms: float | None


async def get_rate_limits() -> list[RateLimitInfo]:
    return [
        RateLimitInfo(rate_class=rate_class.value, requests_per_minute=limit)
        for rate_class, limit in _RATE_LIMITS.items()
    ]


async def get_error_catalog() -> list[ErrorCatalogEntry]:
    return collect_error_classes()


async def get_testnet_status() -> TestnetStatus:
    settings = Settings()
    if not settings.testnet_base_url:
        return TestnetStatus(reachable=False, latency_ms=None)

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(base_url=settings.testnet_base_url, timeout=5.0) as client:
            response = await client.get("/testnet/health")
    except httpx.HTTPError:
        return TestnetStatus(reachable=False, latency_ms=None)

    elapsed_ms = (time.perf_counter() - started) * 1000
    return TestnetStatus(reachable=response.is_success, latency_ms=elapsed_ms)
