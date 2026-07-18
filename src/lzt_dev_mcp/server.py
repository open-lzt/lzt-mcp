"""Builds the FastMCP app and registers all 29 tools.

The only module that imports FastMCP (D-9, 00-decisions.md): each group's `tools.py` exports
plain undecorated `async def` functions, and this module registers every one via
`mcp.add_tool(Tool.from_function(fn, name=..., description=...))` — never `@mcp.tool` inside a
group module, which would need an already-constructed `mcp` instance and force a circular
import between `server.py` and the group modules.

Confirmed against the installed `fastmcp==3.4.4` API (2026-07-12): `Tool.from_function` and
`FastMCP.add_tool` exist exactly as assumed in the plan (D-9) — no deviation needed.
"""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP
from fastmcp.tools import Tool

from lzt_dev_mcp.eventus import tools as eventus_tools
from lzt_dev_mcp.flow import tools as flow_tools
from lzt_dev_mcp.helpers import tools as helpers_tools
from lzt_dev_mcp.testing import tools as testing_tools

__all__ = ["build_app", "run"]

_TOOL_DESCRIPTIONS: dict[str, str] = {
    # Group A — request testing
    "list_methods": "List pylzt API methods, optionally filtered by namespace/search.",
    "get_method_schema": "Get a method's declared request fields and response model name.",
    "get_model_schema": "Get a response model's JSON Schema by name.",
    "send_request": "Send a real pylzt request; defaults to testnet, prod requires a token.",
    "describe_api": "Search the method catalog by a free-text query.",
    # Group B — flow management
    "list_flows": "List lzt-flow flows for the current tenant.",
    "get_flow": "Get a flow's full spec by id.",
    "create_flow": "Create a new lzt-flow flow from a FlowSpec.",
    "export_flow": "Export a flow as a versioned FlowSpec envelope.",
    "import_flow": "Import a flow from an exported envelope (compile+dry-run gated).",
    "compile_flow": "Compile a flow into an immutable FlowIR.",
    "list_catalog": "List lzt-flow's node catalog (action/logic/trigger types).",
    "list_dynamic_methods": "List pylzt facade methods usable as dynamic flow nodes.",
    "get_dynamic_method": "Describe one dynamic facade method's params and return shape.",
    "create_run": "Start a run of a compiled flow (idempotent on run_key).",
    "list_runs": "List runs for the current tenant.",
    "get_run": "Get a run's current status.",
    "get_run_trace": "Get a run's per-node execution trace.",
    # Group C — helpers
    "get_rate_limits": "List pylzt's published per-RateClass request ceilings.",
    "get_error_catalog": "List pylzt's typed error classes with their carried args.",
    "get_testnet_status": "Check whether the configured lzt-testnet instance is reachable.",
    # Group D — event/subscription management
    "list_subscriptions": "List lzt-eventus subscriptions (admin-key gated).",
    "create_subscription": "Create a new lzt-eventus subscription (webhook/websocket/sse/polling).",
    "poll_pending_events": "Poll pending events for a polling-transport subscription.",
    "confirm_read": "Confirm read progress for a polling-transport subscription up to a seq.",
    "get_event_types": "List lzt-eventus's subscribable event-type catalog.",
    "register_token_account": "Register a new lzt-eventus token account.",
    "list_token_accounts": "List lzt-eventus token accounts (admin-key gated).",
    "get_eventus_status": "Check whether the configured lzt-eventus instance is reachable.",
}

_TOOL_FUNCTIONS = (
    testing_tools.list_methods,
    testing_tools.get_method_schema,
    testing_tools.get_model_schema,
    testing_tools.send_request,
    testing_tools.describe_api,
    flow_tools.list_flows,
    flow_tools.get_flow,
    flow_tools.create_flow,
    flow_tools.export_flow,
    flow_tools.import_flow,
    flow_tools.compile_flow,
    flow_tools.list_catalog,
    flow_tools.list_dynamic_methods,
    flow_tools.get_dynamic_method,
    flow_tools.create_run,
    flow_tools.list_runs,
    flow_tools.get_run,
    flow_tools.get_run_trace,
    helpers_tools.get_rate_limits,
    helpers_tools.get_error_catalog,
    helpers_tools.get_testnet_status,
    eventus_tools.list_subscriptions,
    eventus_tools.create_subscription,
    eventus_tools.poll_pending_events,
    eventus_tools.confirm_read,
    eventus_tools.get_event_types,
    eventus_tools.register_token_account,
    eventus_tools.list_token_accounts,
    eventus_tools.get_eventus_status,
)


def build_app() -> FastMCP:
    mcp = FastMCP("lzt-dev-mcp")
    for fn in _TOOL_FUNCTIONS:
        name = fn.__name__
        mcp.add_tool(Tool.from_function(fn, name=name, description=_TOOL_DESCRIPTIONS[name]))
    return mcp


def run(
    mode: Literal["stdio", "http"] = "stdio", *, host: str = "127.0.0.1", port: int = 8770
) -> None:
    mcp = build_app()
    if mode == "stdio":
        mcp.run(transport="stdio")
    else:
        # Bind loopback explicitly — never rely on the transport's default host for a root process.
        mcp.run(transport="http", host=host, port=port)
