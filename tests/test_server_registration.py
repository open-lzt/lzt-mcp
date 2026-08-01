"""Every declared tool is actually registered, under the name the docs promise.

`build_app` keeps two hand-maintained lists — `_TOOL_FUNCTIONS` and `_TOOL_DESCRIPTIONS`. A
function added without a description fails loudly at import (`KeyError`), but the inverse drift
— a description for a tool nobody registered — is silent, and so is a tool dropped from both
lists at once. This walks the real FastMCP registry instead of either list.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastmcp import Client

from lzt_dev_mcp.server import _TOOL_DESCRIPTIONS, _TOOL_FUNCTIONS


@pytest.mark.asyncio
async def test_every_declared_tool_is_registered(mcp_client: Client[Any]) -> None:
    registered = {tool.name for tool in await mcp_client.list_tools()}
    assert registered == set(_TOOL_DESCRIPTIONS)
    assert registered == {fn.__name__ for fn in _TOOL_FUNCTIONS}


@pytest.mark.asyncio
async def test_registered_tools_carry_their_description(mcp_client: Client[Any]) -> None:
    for tool in await mcp_client.list_tools():
        assert tool.description == _TOOL_DESCRIPTIONS[tool.name]
