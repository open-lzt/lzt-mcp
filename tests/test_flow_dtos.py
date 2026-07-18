"""Unit: a minimal FlowSpec serializes to a JSON body lzt-flow's POST /flows/create accepts."""

from __future__ import annotations

from lzt_dev_mcp.flow.dtos import FlowSpec, NodeSpec
from lzt_dev_mcp.flow.http_client import _flow_spec_to_wire


def test_minimal_flow_spec_serializes_to_expected_wire_shape() -> None:
    spec = FlowSpec(
        name="smoke-test-flow",
        nodes=[NodeSpec(id="n1", type="noop", inputs={})],
        entry_node_id="n1",
    )
    wire = _flow_spec_to_wire(spec)
    assert wire == {
        "name": "smoke-test-flow",
        "nodes": [
            {
                "id": "n1",
                "type": "noop",
                "inputs": {},
                "account_ref": None,
                "edges": {},
                "on_error": None,
                "timeout_s": None,
                "stop_condition": None,
                "children": None,
            }
        ],
        "entry_node_id": "n1",
    }
