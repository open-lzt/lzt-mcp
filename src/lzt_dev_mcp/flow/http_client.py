"""Thin async httpx wrapper over lzt-flow's REST API — one method per endpoint.

No retry/backoff in MVP (dev tool, single local call — see 01-logic.md Group B). Non-2xx
responses raise `UpstreamError(status, body)`. `compile_flow`/`create_run` require
`X-API-Key` per lzt-flow's own `require_api_key` gate on mutating routes; GET-shaped calls send
the header too (cheap, no harm) but don't require it, matching lzt-flow's own posture.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import httpx

from lzt_dev_mcp.errors import UpstreamError
from lzt_dev_mcp.flow.dtos import (
    CatalogNodeResponse,
    CreateRunRequest,
    DynamicMethodDetailResponse,
    DynamicMethodParamResponse,
    DynamicMethodResponse,
    FlowCompiledResponse,
    FlowCreatedResponse,
    FlowDetailResponse,
    FlowExportEnvelope,
    FlowSpec,
    FlowSummary,
    ImportResultResponse,
    InputSpec,
    NodeCategory,
    NodeSpec,
    RunResponse,
    RunStatus,
    RunSummary,
    RunTraceEntry,
    StopConditionSpec,
)

__all__ = ["FlowHttpClient"]


def _input_spec_from_wire(body: dict[str, Any]) -> InputSpec:
    return InputSpec(literal=body.get("literal"), ref=body.get("ref"))


def _stop_condition_from_wire(body: dict[str, Any] | None) -> StopConditionSpec | None:
    if body is None:
        return None
    return StopConditionSpec(
        output_key=body["output_key"],
        equals=body["equals"],
        action=body["action"],
        goto_node_id=body.get("goto_node_id"),
    )


def _node_spec_from_wire(body: dict[str, Any]) -> NodeSpec:
    children = body.get("children")
    return NodeSpec(
        id=body["id"],
        type=body["type"],
        inputs={name: _input_spec_from_wire(v) for name, v in (body.get("inputs") or {}).items()},
        account_ref=body.get("account_ref"),
        edges=body.get("edges") or {},
        on_error=body.get("on_error"),
        timeout_s=body.get("timeout_s"),
        stop_condition=_stop_condition_from_wire(body.get("stop_condition")),
        children=tuple(_node_spec_from_wire(c) for c in children) if children else None,
    )


def _flow_spec_from_wire(body: dict[str, Any]) -> FlowSpec:
    return FlowSpec(
        name=body["name"],
        nodes=[_node_spec_from_wire(n) for n in body["nodes"]],
        entry_node_id=body["entry_node_id"],
    )


def _node_spec_to_wire(spec: NodeSpec) -> dict[str, Any]:
    return {
        "id": spec.id,
        "type": spec.type,
        "inputs": {name: dataclasses.asdict(v) for name, v in spec.inputs.items()},
        "account_ref": spec.account_ref,
        "edges": spec.edges,
        "on_error": spec.on_error,
        "timeout_s": spec.timeout_s,
        "stop_condition": dataclasses.asdict(spec.stop_condition) if spec.stop_condition else None,
        "children": [_node_spec_to_wire(c) for c in spec.children] if spec.children else None,
    }


def _flow_spec_to_wire(spec: FlowSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "nodes": [_node_spec_to_wire(n) for n in spec.nodes],
        "entry_node_id": spec.entry_node_id,
    }


class FlowHttpClient:
    def __init__(self, base_url: str, api_key: str | None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._api_key} if self._api_key else {}

    async def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=30.0) as client:
            response = await client.request(method, path, json=json, headers=self._headers())
        if not response.is_success:
            raise UpstreamError(status=response.status_code, body=response.text)
        return response.json()

    async def list_flows(self) -> list[FlowSummary]:
        body = await self._request("GET", "/flows/list")
        return [FlowSummary(flow_id=item["flow_id"], name=item["name"]) for item in body]

    async def get_flow(self, flow_id: str) -> FlowDetailResponse:
        body = await self._request("GET", f"/flows/{flow_id}/get")
        return FlowDetailResponse(
            flow_id=body["flow_id"], name=body["name"], spec=_flow_spec_from_wire(body["spec"])
        )

    async def create_flow(self, spec: FlowSpec) -> FlowCreatedResponse:
        body = await self._request("POST", "/flows/create", json=_flow_spec_to_wire(spec))
        return FlowCreatedResponse(flow_id=body["flow_id"])

    async def export_flow(self, flow_id: str) -> FlowExportEnvelope:
        body = await self._request("GET", f"/flows/{flow_id}/export")
        return FlowExportEnvelope(
            schema_version=body["schema_version"], flow=_flow_spec_from_wire(body["flow"])
        )

    async def import_flow(self, envelope: FlowExportEnvelope) -> ImportResultResponse:
        wire = {
            "schema_version": envelope.schema_version,
            "flow": _flow_spec_to_wire(envelope.flow),
        }
        body = await self._request("POST", "/flows/import", json=wire)
        return ImportResultResponse(flow_id=body["flow_id"], name=body["name"])

    async def compile_flow(self, flow_id: str) -> FlowCompiledResponse:
        body = await self._request("POST", f"/flows/{flow_id}/compile")
        return FlowCompiledResponse(flow_ir_id=body["flow_ir_id"], node_count=body["node_count"])

    async def list_catalog(self) -> list[CatalogNodeResponse]:
        body = await self._request("GET", "/catalog/list")
        return [
            CatalogNodeResponse(
                key=item["key"],
                category=NodeCategory(item["category"]),
                input_schema=item["input_schema"],
                idempotent=item["idempotent"],
            )
            for item in body
        ]

    async def list_dynamic_methods(self, facade: str) -> list[DynamicMethodResponse]:
        body = await self._request("GET", f"/catalog/dynamic_methods/{facade}")
        return [
            DynamicMethodResponse(
                name=item["name"],
                params=[DynamicMethodParamResponse(**p) for p in item["params"]],
            )
            for item in body
        ]

    async def get_dynamic_method(self, facade: str, method: str) -> DynamicMethodDetailResponse:
        body = await self._request("GET", f"/catalog/dynamic_methods/{facade}/{method}")
        return DynamicMethodDetailResponse(
            name=body["name"],
            params=[DynamicMethodParamResponse(**p) for p in body["params"]],
            returns=body["returns"],
        )

    async def create_run(self, req: CreateRunRequest) -> RunResponse:
        body = await self._request(
            "POST", "/runs/create", json={"flow_id": req.flow_id, "run_key": req.run_key}
        )
        return RunResponse(run_id=body["run_id"], status=RunStatus(body["status"]))

    async def list_runs(self) -> list[RunSummary]:
        body = await self._request("GET", "/runs/list")
        return [
            RunSummary(
                run_id=item["run_id"],
                flow_id=item["flow_id"],
                status=RunStatus(item["status"]),
                created_at=item["created_at"],
            )
            for item in body
        ]

    async def get_run(self, run_id: str) -> RunResponse:
        body = await self._request("GET", f"/runs/{run_id}/get")
        return RunResponse(run_id=body["run_id"], status=RunStatus(body["status"]))

    async def get_run_trace(self, run_id: str) -> list[RunTraceEntry]:
        body = await self._request("GET", f"/runs/{run_id}/trace")
        return [
            RunTraceEntry(
                node_id=item["node_id"],
                iteration_key=item["iteration_key"],
                node_type=item["node_type"],
                inputs=item["inputs"],
                output=item["output"],
                started_at=item["started_at"],
                completed_at=item["completed_at"],
            )
            for item in body
        ]
