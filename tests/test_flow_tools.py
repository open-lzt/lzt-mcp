"""e2e: full round-trip against a running local lzt-flow dev instance."""

from __future__ import annotations

import os
from typing import Any

import pytest

from lzt_dev_mcp.flow.dtos import CreateRunRequest, FlowSpec, InputSpec, NodeSpec
from lzt_dev_mcp.flow.tools import (
    compile_flow,
    create_flow,
    create_run,
    get_run,
    get_run_trace,
    list_catalog,
)

pytestmark = pytest.mark.e2e


def _literal_input_for(schema: dict[str, Any]) -> dict[str, InputSpec]:
    """Builds a minimal valid `inputs` mapping from a node's declared JSON Schema so this
    test stays correct even if lzt-flow's catalog ordering/shape changes — any required
    integer field gets `1`, any required string field gets a placeholder string."""
    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])
    inputs: dict[str, InputSpec] = {}
    for field_name in required:
        field_type = properties.get(field_name, {}).get("type")
        literal: str | int = 1 if field_type == "integer" else "placeholder"
        inputs[field_name] = InputSpec(literal=literal)
    return inputs


@pytest.mark.asyncio
async def test_flow_round_trip() -> None:
    os.environ["LZT_DEV_MCP_LZT_FLOW_BASE_URL"] = "http://127.0.0.1:8000"
    catalog = await list_catalog()
    assert len(catalog) > 0

    node = catalog[0]
    spec = FlowSpec(
        name="e2e-smoke",
        nodes=[NodeSpec(id="n1", type=node.key, inputs=_literal_input_for(node.input_schema))],
        entry_node_id="n1",
    )
    created = await create_flow(spec)
    compiled = await compile_flow(created.flow_id)
    assert compiled.node_count == 1

    run = await create_run(CreateRunRequest(flow_id=created.flow_id))
    status = await get_run(run.run_id)
    assert status.run_id == run.run_id

    trace = await get_run_trace(run.run_id)
    assert isinstance(trace, list)
