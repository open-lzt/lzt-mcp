"""Local typed DTO mirrors of lzt-eventus's REST API, one field per confirmed route.

Every field cited against lzt-eventus source (`web/routes/{events,subscriptions,
token_accounts,meta}.py`, `web/schemas/{dtos,envelopes,events}.py`) — no lzt-eventus code is
imported, these are independent mirrors so this repo has zero import coupling to lzt-eventus.

`ctx` (per-transport knobs: WebhookCtx/WebSocketCtx/SseCtx/PollingCtx) and `scope` (NoScope/
CategoryScope/AccountScope) are polymorphic discriminated unions on the wire — mirrored here as
`dict[str, object]` passthrough rather than reconstructed per-variant, matching this repo's own
`CatalogNodeResponse.input_schema` precedent for opaque nested JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TransportKind(StrEnum):
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    SSE = "sse"
    POLLING = "polling"


@dataclass(frozen=True)
class SubscriptionCreate:
    transport: TransportKind
    endpoint: str
    event_types: list[str]
    ctx: dict[str, object] | None = None
    scope: dict[str, object] = field(default_factory=dict)
    backfill: bool = False


@dataclass(frozen=True)
class SubscriptionOut:
    subscription_id: str
    transport: TransportKind
    endpoint: str
    event_types: list[str]
    scope: dict[str, object]
    ctx: dict[str, object]
    active: bool
    created_at: str
    secret: str | None = None
    stream_token: str | None = None


@dataclass(frozen=True)
class PendingEventOut:
    seq: int
    event_type: str
    data: dict[str, object]


@dataclass(frozen=True)
class PendingEventsOut:
    subscription_id: str
    items: list[PendingEventOut]
    next_seq: int
    last_read_seq: int
    drained: bool
    committed: bool


@dataclass(frozen=True)
class ReadEventsResult:
    subscription_id: str
    last_seq: int


@dataclass(frozen=True)
class TokenAccountCreate:
    token: str
    alias: str
    metadata: dict[str, str] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TokenAccountOut:
    account_id: str
    metadata: dict[str, str]
    categories: list[str]
    active: bool
    created_at: str
    token: str | None = None


@dataclass(frozen=True)
class EventusHealth:
    ok: bool
