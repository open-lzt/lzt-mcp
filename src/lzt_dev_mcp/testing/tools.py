"""Group A MCP tools: list/introspect pylzt methods+models, send a real request.

Plain undecorated `async def` functions per D-9 (00-decisions.md) — `server.py` is the only
module that imports FastMCP and registers these via `mcp.add_tool(Tool.from_function(...))`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel
from pylzt.methods.base import BaseMethod

from lzt_dev_mcp.catalog.errors_catalog import KNOWN_HTTP_STATUS
from lzt_dev_mcp.catalog.models import collect_response_models
from lzt_dev_mcp.catalog.registry import collect_base_methods
from lzt_dev_mcp.config import Settings
from lzt_dev_mcp.errors import MethodNotFound, ModelNotFound, UpstreamError
from lzt_dev_mcp.testing.client_factory import build_client

__all__ = [
    "MethodSchema",
    "MethodSummary",
    "RequestResult",
    "describe_api",
    "get_method_schema",
    "get_model_schema",
    "list_methods",
    "send_request",
]


@dataclass(frozen=True)
class MethodSummary:
    name: str
    http_method: str
    path: str
    api_target: str
    returning: str | None


@dataclass(frozen=True)
class MethodSchema:
    name: str
    fields: dict[str, str]
    required_fields: tuple[str, ...]
    returning: str | None


@dataclass(frozen=True)
class RequestResult:
    status: int
    body: dict[str, object]
    elapsed_ms: float


@lru_cache(maxsize=1)
def _method_catalog() -> dict[str, type[BaseMethod]]:  # type: ignore[type-arg]
    return {cls.__name__: cls for cls in collect_base_methods()}


@lru_cache(maxsize=1)
def _model_catalog() -> dict[str, type[BaseModel]]:
    return collect_response_models()


def _returning_name(method_cls: type[BaseMethod]) -> str | None:  # type: ignore[type-arg]
    returning = method_cls.__returning__
    return returning.__name__ if isinstance(returning, type) else None


def _summarize(name: str, method_cls: type[BaseMethod]) -> MethodSummary:  # type: ignore[type-arg]
    return MethodSummary(
        name=name,
        http_method=method_cls.__http_method__.value,
        path=method_cls.__url__,
        api_target=method_cls.__api__.value,
        returning=_returning_name(method_cls),
    )


def _search_catalog(query: str | None, namespace: str | None) -> list[MethodSummary]:
    catalog = _method_catalog()
    needle = query.lower() if query else None
    results: list[MethodSummary] = []
    for name, method_cls in catalog.items():
        if namespace and method_cls.__api__.value != namespace:
            continue
        if (
            needle
            and needle not in name.lower()
            and needle not in (method_cls.__doc__ or "").lower()
        ):
            continue
        results.append(_summarize(name, method_cls))
    return sorted(results, key=lambda summary: summary.name)


async def list_methods(
    namespace: str | None = None, search: str | None = None
) -> list[MethodSummary]:
    return _search_catalog(search, namespace)


async def describe_api(query: str) -> list[MethodSummary]:
    return _search_catalog(query, namespace=None)


async def get_method_schema(method_name: str) -> MethodSchema:
    method_cls = _method_catalog().get(method_name)
    if method_cls is None:
        raise MethodNotFound(method_name)
    fields = {
        field_name: str(field_info.annotation)
        for field_name, field_info in method_cls.model_fields.items()
    }
    required = tuple(
        field_name
        for field_name, field_info in method_cls.model_fields.items()
        if field_info.is_required()
    )
    return MethodSchema(
        name=method_name,
        fields=fields,
        required_fields=required,
        returning=_returning_name(method_cls),
    )


async def get_model_schema(model_name: str) -> dict[str, object]:
    model_cls = _model_catalog().get(model_name)
    if model_cls is None:
        raise ModelNotFound(model_name)
    return model_cls.model_json_schema()


async def send_request(
    method_name: str,
    params: dict[str, object],
    target: Literal["testnet", "prod"] = "testnet",
    token: str | None = None,
) -> RequestResult:
    method_cls = _method_catalog().get(method_name)
    if method_cls is None:
        raise MethodNotFound(method_name)

    settings = Settings()
    client = build_client(target, token, settings)
    method_instance = method_cls(**params)

    started = time.perf_counter()
    try:
        result = await client.execute(method_instance)
    except Exception as exc:  # noqa: BLE001 — narrow pylzt's typed error to our own boundary type
        status = KNOWN_HTTP_STATUS.get(type(exc).__name__) or 0
        raise UpstreamError(status=status, body=str(exc)) from exc
    elapsed_ms = (time.perf_counter() - started) * 1000

    body = result.model_dump() if isinstance(result, BaseModel) else {"result": result}
    return RequestResult(status=200, body=body, elapsed_ms=elapsed_ms)
