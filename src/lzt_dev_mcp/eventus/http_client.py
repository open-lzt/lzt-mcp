"""Thin async httpx wrapper over lzt-eventus's REST API — one method per endpoint.

No retry/backoff in MVP (dev tool, single local call — same posture as `flow/http_client.py`).
Non-2xx responses raise `UpstreamError(status, body)`. Every call sends the admin key via
`X-API-Key` — every route this client touches is `AdminDep`-gated in lzt-eventus.
"""

from __future__ import annotations

from typing import Any

import httpx

from lzt_dev_mcp.errors import UpstreamError
from lzt_dev_mcp.eventus.dtos import (
    EventusHealth,
    PendingEventOut,
    PendingEventsOut,
    ReadEventsResult,
    SubscriptionCreate,
    SubscriptionOut,
    TokenAccountCreate,
    TokenAccountOut,
    TransportKind,
)

__all__ = ["EventusHttpClient"]


def _subscription_from_wire(body: dict[str, Any]) -> SubscriptionOut:
    return SubscriptionOut(
        subscription_id=body["subscription_id"],
        transport=TransportKind(body["transport"]),
        endpoint=body["endpoint"],
        event_types=body["event_types"],
        scope=body["scope"],
        ctx=body["ctx"],
        active=body["active"],
        created_at=body["created_at"],
        secret=body.get("secret"),
        stream_token=body.get("stream_token"),
    )


def _token_account_from_wire(body: dict[str, Any]) -> TokenAccountOut:
    return TokenAccountOut(
        account_id=body["account_id"],
        metadata=body["metadata"],
        categories=body["categories"],
        active=body["active"],
        created_at=body["created_at"],
        token=body.get("token"),
    )


class EventusHttpClient:
    def __init__(self, base_url: str, admin_api_key: str | None) -> None:
        self._base_url = base_url.rstrip("/")
        self._admin_api_key = admin_api_key

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._admin_api_key} if self._admin_api_key else {}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=30.0) as client:
            response = await client.request(
                method, path, params=params, json=json, headers=self._headers()
            )
        if not response.is_success:
            raise UpstreamError(status=response.status_code, body=response.text)
        return response.json()

    async def list_subscriptions(self) -> list[SubscriptionOut]:
        body = await self._request("GET", "/subscriptions/list")
        return [_subscription_from_wire(item) for item in body["items"]]

    async def create_subscription(self, spec: SubscriptionCreate) -> SubscriptionOut:
        wire = {
            "transport": spec.transport.value,
            "endpoint": spec.endpoint,
            "event_types": spec.event_types,
            "ctx": spec.ctx,
            "scope": spec.scope,
            "backfill": spec.backfill,
        }
        body = await self._request("POST", "/subscriptions/create", json=wire)
        return _subscription_from_wire(body["data"])

    async def poll_pending_events(
        self, subscription_id: str, event_type: list[str] | None, limit: int
    ) -> PendingEventsOut:
        params: dict[str, Any] = {"subscription_id": subscription_id, "limit": limit}
        if event_type:
            params["event_type"] = event_type
        body = await self._request("GET", "/events/pending", params=params)
        return PendingEventsOut(
            subscription_id=body["subscription_id"],
            items=[
                PendingEventOut(seq=i["seq"], event_type=i["event_type"], data=i["data"])
                for i in body["items"]
            ],
            next_seq=body["next_seq"],
            last_read_seq=body["last_read_seq"],
            drained=body["drained"],
            committed=body["committed"],
        )

    async def confirm_read(self, subscription_id: str, up_to_seq: int) -> ReadEventsResult:
        wire = {"subscription_id": subscription_id, "up_to_seq": up_to_seq}
        body = await self._request("POST", "/events/read_events", json=wire)
        return ReadEventsResult(subscription_id=body["subscription_id"], last_seq=body["last_seq"])

    async def get_event_types(self) -> list[str]:
        body = await self._request("GET", "/event-types")
        return list(body["data"])

    async def register_token_account(self, spec: TokenAccountCreate) -> TokenAccountOut:
        wire = {
            "token": spec.token,
            "alias": spec.alias,
            "metadata": spec.metadata,
            "categories": spec.categories,
        }
        body = await self._request("POST", "/tokens/register", json=wire)
        return _token_account_from_wire(body["data"])

    async def list_token_accounts(self) -> list[TokenAccountOut]:
        body = await self._request("GET", "/tokens/list")
        return [_token_account_from_wire(item) for item in body["items"]]

    async def get_status(self) -> EventusHealth:
        try:
            await self._request("GET", "/healthz")
        except UpstreamError:
            return EventusHealth(ok=False)
        return EventusHealth(ok=True)
