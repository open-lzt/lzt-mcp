"""Typed error hierarchy for lzt-dev-mcp. Never raised without args where args are declared."""

from __future__ import annotations

from dataclasses import dataclass


class DevMcpError(Exception):
    """Base for every typed error raised by this server. Never raised directly."""


@dataclass
class MethodNotFound(DevMcpError):
    name: str


@dataclass
class ModelNotFound(DevMcpError):
    name: str


@dataclass
class ProdBlocked(DevMcpError):
    """Raised whenever target='prod' is requested without an explicit, non-empty token.

    Carries nothing — the point is the type, not the data. No env-var fallback exists;
    see 00-decisions.md D-4.
    """


@dataclass
class TestnetUnavailable(DevMcpError):
    """Raised when target='testnet' (the default) but no testnet_base_url is configured.

    Never silently falls through to prod — see 00-decisions.md D-4.
    """


@dataclass
class UpstreamError(DevMcpError):
    status: int
    body: str


@dataclass
class ModelDeclarationError(DevMcpError):
    """Raised when two response models collide on `__name__` during catalog collection —
    fail loud instead of silently overwriting one with the other."""

    name: str
    first_module: str
    second_module: str
