"""Local typed DTO mirrors of lzt-flow's REST API, per 03-types.md (frozen contract).

Every field cited against lzt-flow source (`open-lzt/app/api/flow_routes.py`,
`run_routes.py`, `catalog_routes.py`, `domain/flow_engine/spec.py`, `domain/flow_engine/model.py`,
`domain/catalog/registry.py`) — no lzt-flow code is imported, these are independent mirrors so
this repo has zero import coupling to the lzt-flow codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal


@dataclass(frozen=True)
class InputSpec:
    literal: str | int | float | bool | None = None
    ref: str | None = None


@dataclass(frozen=True)
class StopConditionSpec:
    output_key: str
    equals: str | int | float | bool
    action: Literal["abort", "goto"]
    goto_node_id: str | None = None


@dataclass(frozen=True)
class NodeSpec:
    id: str
    type: str
    inputs: dict[str, InputSpec] = field(default_factory=dict)
    account_ref: str | None = None
    edges: dict[str, str] = field(default_factory=dict)
    on_error: str | None = None
    timeout_s: int | None = None
    stop_condition: StopConditionSpec | None = None
    children: tuple[NodeSpec, ...] | None = None


@dataclass(frozen=True)
class FlowSpec:
    name: str
    nodes: list[NodeSpec]
    entry_node_id: str


@dataclass(frozen=True)
class FlowCreatedResponse:
    flow_id: str


@dataclass(frozen=True)
class FlowSummary:
    flow_id: str
    name: str


@dataclass(frozen=True)
class FlowDetailResponse:
    flow_id: str
    name: str
    spec: FlowSpec


@dataclass(frozen=True)
class FlowExportEnvelope:
    flow: FlowSpec
    schema_version: int = 1


@dataclass(frozen=True)
class ImportResultResponse:
    flow_id: str
    name: str


@dataclass(frozen=True)
class FlowCompiledResponse:
    flow_ir_id: str
    node_count: int


@dataclass(frozen=True)
class CreateRunRequest:
    flow_id: str
    run_key: str | None = None


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RunResponse:
    run_id: str
    status: RunStatus


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    flow_id: str
    status: RunStatus
    created_at: str


@dataclass(frozen=True)
class RunTraceEntry:
    node_id: str
    iteration_key: str | None
    node_type: str
    inputs: dict[str, str | int | float | bool | None]
    output: dict[str, str | int | float | bool | None]
    started_at: str
    completed_at: str


class NodeCategory(StrEnum):
    ACTION = "action"
    LOGIC = "logic"
    TRIGGER = "trigger"


@dataclass(frozen=True)
class CatalogNodeResponse:
    key: str
    category: NodeCategory
    input_schema: dict[str, object]
    idempotent: bool


@dataclass(frozen=True)
class DynamicMethodParamResponse:
    name: str
    type_str: str
    required: bool


@dataclass(frozen=True)
class DynamicMethodResponse:
    name: str
    params: list[DynamicMethodParamResponse]


@dataclass(frozen=True)
class DynamicMethodDetailResponse:
    name: str
    params: list[DynamicMethodParamResponse]
    returns: dict[str, object]
