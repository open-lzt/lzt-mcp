"""Group D MCP tools: 8 thin wrappers over `EventusHttpClient`, one per lzt-eventus endpoint.

Plain undecorated `async def` functions per D-9, matching `flow/tools.py`'s pattern exactly —
a module-level lazy singleton client keyed off `Settings` since an MCP tool call can't take the
client as a parameter.
"""

from __future__ import annotations

from functools import lru_cache

from lzt_dev_mcp.config import Settings
from lzt_dev_mcp.eventus.dtos import (
    EventusHealth,
    PendingEventsOut,
    ReadEventsResult,
    SubscriptionCreate,
    SubscriptionOut,
    TokenAccountCreate,
    TokenAccountOut,
)
from lzt_dev_mcp.eventus.http_client import EventusHttpClient

__all__ = [
    "confirm_read",
    "create_subscription",
    "get_event_types",
    "get_eventus_status",
    "list_subscriptions",
    "list_token_accounts",
    "poll_pending_events",
    "register_token_account",
]


@lru_cache(maxsize=1)
def _client() -> EventusHttpClient:
    settings = Settings()
    return EventusHttpClient(
        base_url=settings.lzt_eventus_base_url, admin_api_key=settings.lzt_eventus_admin_api_key
    )


async def list_subscriptions() -> list[SubscriptionOut]:
    return await _client().list_subscriptions()


async def create_subscription(spec: SubscriptionCreate) -> SubscriptionOut:
    return await _client().create_subscription(spec)


async def poll_pending_events(
    subscription_id: str, event_type: list[str] | None = None, limit: int = 100
) -> PendingEventsOut:
    return await _client().poll_pending_events(subscription_id, event_type, limit)


async def confirm_read(subscription_id: str, up_to_seq: int) -> ReadEventsResult:
    return await _client().confirm_read(subscription_id, up_to_seq)


async def get_event_types() -> list[str]:
    return await _client().get_event_types()


async def register_token_account(spec: TokenAccountCreate) -> TokenAccountOut:
    return await _client().register_token_account(spec)


async def list_token_accounts() -> list[TokenAccountOut]:
    return await _client().list_token_accounts()


async def get_eventus_status() -> EventusHealth:
    return await _client().get_status()
