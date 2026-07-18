"""Unit: catalog registry covers >=190 methods; model registry is non-empty."""

from __future__ import annotations

import pytest

from lzt_dev_mcp.catalog.models import collect_response_models
from lzt_dev_mcp.catalog.registry import collect_base_methods
from lzt_dev_mcp.errors import ModelDeclarationError


def test_collect_base_methods_covers_the_full_catalog() -> None:
    methods = collect_base_methods()
    assert len(methods) >= 190
    assert len({cls.__name__ for cls in methods}) == len(methods)


def test_collect_response_models_builds_a_full_registry_from_the_real_catalog() -> None:
    """pylzt used to ship two DISTINCT `StatusMessageResponse` models (market vs forum
    namespace) sharing a bare class name, which made this raise `ModelDeclarationError` for
    real. Fixed upstream in pylzt (renamed to `MarketStatusMessageResponse` /
    `ForumStatusMessageResponse` at the generator level, not just the generated file) — this
    now proves the real catalog builds a full registry without hitting R-4's fail-loud guard."""
    models = collect_response_models()
    assert len(models) > 0


def test_collect_response_models_raises_loud_on_name_collision() -> None:
    from pydantic import BaseModel

    class Dup(BaseModel):
        pass

    Dup.__module__ = "fake.module.one"
    Dup2 = type("Dup", (BaseModel,), {"__module__": "fake.module.two"})

    class _FakeMethod:
        __returning__ = Dup

    class _FakeMethod2:
        __returning__ = Dup2

    import lzt_dev_mcp.catalog.models as models_module

    original = models_module.collect_base_methods
    # fakes deliberately don't satisfy BaseMethod[Any] — simulates a real name collision
    models_module.collect_base_methods = lambda: [_FakeMethod, _FakeMethod2]  # type: ignore[assignment]
    try:
        with pytest.raises(ModelDeclarationError):
            collect_response_models()
    finally:
        models_module.collect_base_methods = original
