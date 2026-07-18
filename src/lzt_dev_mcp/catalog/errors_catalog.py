"""Introspects `pylzt.errors` for every wire-facing `LztError` subclass."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from functools import lru_cache

import pylzt.errors as lztforge_errors
from pylzt.errors import LztError

__all__ = ["ErrorCatalogEntry", "collect_error_classes"]

# LztError.check() classmethods encode the real status match, but that logic isn't reflectable
# generically — this table documents the known status each __wire__ error class matches on
# (cross-checked against pylzt/errors.py's own check() bodies). Unmapped/ambiguous classes
# (retryable/captcha/5xx-range) report None rather than guessing.
KNOWN_HTTP_STATUS: dict[str, int | None] = {
    "RateLimited": 429,
    "AuthFailed": 401,
    "Forbidden": 403,
    "NotFound": 404,
    "BadRequest": 400,
}


@dataclass(frozen=True)
class ErrorCatalogEntry:
    name: str
    args: tuple[str, ...]
    http_status: int | None


def _init_arg_names(cls: type[LztError]) -> tuple[str, ...]:
    signature = inspect.signature(cls.__init__)
    return tuple(name for name in signature.parameters if name != "self")


@lru_cache(maxsize=1)
def collect_error_classes() -> list[ErrorCatalogEntry]:
    """Introspects `pylzt.errors` module members via `inspect.getmembers`, filters to
    `LztError` subclasses, and reads each `__init__` signature for its typed-arg names.
    Cached — pylzt's error hierarchy is fixed for the process lifetime."""
    entries: list[ErrorCatalogEntry] = []
    for _name, obj in inspect.getmembers(lztforge_errors, inspect.isclass):
        if not issubclass(obj, LztError) or obj is LztError:
            continue
        entries.append(
            ErrorCatalogEntry(
                name=obj.__name__,
                args=_init_arg_names(obj),
                http_status=KNOWN_HTTP_STATUS.get(obj.__name__),
            )
        )
    return entries
