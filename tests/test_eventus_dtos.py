"""Unit: eventus wire-parsing helpers round-trip lzt-eventus's real response shapes."""

from __future__ import annotations

from lzt_dev_mcp.eventus.dtos import TransportKind
from lzt_dev_mcp.eventus.http_client import _subscription_from_wire, _token_account_from_wire


def test_subscription_from_wire_parses_full_shape() -> None:
    wire = {
        "subscription_id": "sub-1",
        "transport": "polling",
        "endpoint": "n/a",
        "event_types": ["order.paid"],
        "scope": {"kind": "no_scope"},
        "ctx": {"kind": "polling", "poll_delay_seconds": 1},
        "active": True,
        "created_at": "2026-07-12T00:00:00Z",
        "secret": "s3cr3t",
        "stream_token": None,
    }
    sub = _subscription_from_wire(wire)
    assert sub.subscription_id == "sub-1"
    assert sub.transport is TransportKind.POLLING
    assert sub.secret == "s3cr3t"


def test_token_account_from_wire_redacts_token_by_default() -> None:
    wire = {
        "account_id": "acc-1",
        "metadata": {},
        "categories": [],
        "active": True,
        "created_at": "2026-07-12T00:00:00Z",
    }
    account = _token_account_from_wire(wire)
    assert account.token is None
    assert account.account_id == "acc-1"
