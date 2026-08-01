"""Group-A catalog tools: the four that `test_send_request_live_testnet.py` does not reach.

`send_request` was the only tool with a test, so a broken namespace filter or an inverted
required-fields computation shipped green. These assert behaviour, not non-None-ness.
"""

from __future__ import annotations

import pytest

from lzt_dev_mcp.errors import MethodNotFound, ModelNotFound
from lzt_dev_mcp.testing.tools import (
    _method_catalog,  # noqa: PLC2701 — the needle is matched against docstrings the DTO omits
    describe_api,
    get_method_schema,
    get_model_schema,
    list_methods,
)


@pytest.mark.asyncio
async def test_list_methods_without_filters_returns_the_whole_catalog() -> None:
    methods = await list_methods()
    assert len(methods) > 190
    assert methods == sorted(methods, key=lambda summary: summary.name)


@pytest.mark.asyncio
async def test_list_methods_namespace_filter_is_exclusive_and_narrowing() -> None:
    everything = await list_methods()
    market_only = await list_methods(namespace="market")
    assert 0 < len(market_only) < len(everything)
    assert {summary.api_target for summary in market_only} == {"market"}


@pytest.mark.asyncio
async def test_list_methods_search_narrows_and_every_hit_carries_the_needle() -> None:
    catalog = {summary.name: summary for summary in await list_methods()}
    matches = await list_methods(search="category")
    assert matches, "no method name or docstring contains 'category'"
    assert len(matches) < len(catalog)
    # The needle is matched against the class name OR its docstring, so assert against both —
    # asserting the name alone would fail on a legitimate docstring-only hit.
    for summary in matches:
        method_cls = _method_catalog()[summary.name]
        haystack = f"{summary.name} {method_cls.__doc__ or ''}".lower()
        assert "category" in haystack


@pytest.mark.asyncio
async def test_describe_api_searches_across_every_namespace() -> None:
    scoped = await list_methods(namespace="market", search="category")
    unscoped = await describe_api("category")
    assert len(unscoped) >= len(scoped)


@pytest.mark.asyncio
async def test_get_method_schema_separates_required_from_optional() -> None:
    name = (await list_methods())[0].name
    schema = await get_method_schema(name)
    assert schema.name == name
    assert set(schema.required_fields) <= set(schema.fields)


@pytest.mark.asyncio
async def test_get_method_schema_unknown_name_raises() -> None:
    with pytest.raises(MethodNotFound):
        await get_method_schema("NoSuchMethodAnywhere")


@pytest.mark.asyncio
async def test_get_model_schema_returns_a_json_schema() -> None:
    name = next(
        summary.returning for summary in await list_methods() if summary.returning is not None
    )
    schema = await get_model_schema(name)
    assert schema["type"] == "object"


@pytest.mark.asyncio
async def test_get_model_schema_unknown_name_raises() -> None:
    with pytest.raises(ModelNotFound):
        await get_model_schema("NoSuchModelAnywhere")
