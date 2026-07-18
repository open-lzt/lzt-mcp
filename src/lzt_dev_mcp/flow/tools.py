"""Group B MCP tools: 13 thin wrappers over `FlowHttpClient`, one per lzt-flow endpoint.

Plain undecorated `async def` functions per D-9 — signatures take only the args an MCP caller
supplies (no `FlowHttpClient` parameter: a tool call arrives as name+params over the wire, so
the client instance is a lazily-built module-level singleton keyed off `Settings`, mirroring
`testing/tools.py`'s catalog-caching pattern).
"""

from __future__ import annotations

from functools import lru_cache

from lzt_dev_mcp.config import Settings
from lzt_dev_mcp.flow.dtos import (
    CatalogNodeResponse,
    CreateRunRequest,
    DynamicMethodDetailResponse,
    DynamicMethodResponse,
    FlowCompiledResponse,
    FlowCreatedResponse,
    FlowDetailResponse,
    FlowExportEnvelope,
    FlowSpec,
    FlowSummary,
    ImportResultResponse,
    RunResponse,
    RunSummary,
    RunTraceEntry,
)
from lzt_dev_mcp.flow.http_client import FlowHttpClient

__all__ = [
    "compile_flow",
    "create_flow",
    "create_run",
    "export_flow",
    "get_dynamic_method",
    "get_flow",
    "get_run",
    "get_run_trace",
    "import_flow",
    "list_catalog",
    "list_dynamic_methods",
    "list_flows",
    "list_runs",
]


@lru_cache(maxsize=1)
def _client() -> FlowHttpClient:
    settings = Settings()
    return FlowHttpClient(base_url=settings.lzt_flow_base_url, api_key=settings.lzt_flow_api_key)


async def list_flows() -> list[FlowSummary]:
    return await _client().list_flows()


async def get_flow(flow_id: str) -> FlowDetailResponse:
    return await _client().get_flow(flow_id)


async def create_flow(spec: FlowSpec) -> FlowCreatedResponse:
    return await _client().create_flow(spec)


async def export_flow(flow_id: str) -> FlowExportEnvelope:
    return await _client().export_flow(flow_id)


async def import_flow(envelope: FlowExportEnvelope) -> ImportResultResponse:
    return await _client().import_flow(envelope)


async def compile_flow(flow_id: str) -> FlowCompiledResponse:
    return await _client().compile_flow(flow_id)


async def list_catalog() -> list[CatalogNodeResponse]:
    return await _client().list_catalog()


async def list_dynamic_methods(facade: str) -> list[DynamicMethodResponse]:
    return await _client().list_dynamic_methods(facade)


async def get_dynamic_method(facade: str, method: str) -> DynamicMethodDetailResponse:
    return await _client().get_dynamic_method(facade, method)


async def create_run(req: CreateRunRequest) -> RunResponse:
    return await _client().create_run(req)


async def list_runs() -> list[RunSummary]:
    return await _client().list_runs()


async def get_run(run_id: str) -> RunResponse:
    return await _client().get_run(run_id)


async def get_run_trace(run_id: str) -> list[RunTraceEntry]:
    return await _client().get_run_trace(run_id)
