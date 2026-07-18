"""Response-model registry: every distinct `__returning__` model, keyed by class name."""

from __future__ import annotations

from pydantic import BaseModel

from lzt_dev_mcp.catalog.registry import collect_base_methods
from lzt_dev_mcp.errors import ModelDeclarationError

__all__ = ["collect_response_models", "collect_base_methods"]


def collect_response_models() -> dict[str, type[BaseModel]]:
    """Walks the methods from `collect_base_methods()`, extracts each `__returning__` that is
    not the `Passthrough` sentinel, keyed by class `__name__`. A name collision (two models
    sharing a name across market/forum/antipublic) raises `ModelDeclarationError` — fail loud,
    never a silent overwrite.
    """
    models: dict[str, type[BaseModel]] = {}
    for method_cls in collect_base_methods():
        returning = method_cls.__returning__
        if returning is None or not isinstance(returning, type):
            continue  # None (unreachable for a valid subclass) or the Passthrough() sentinel
        existing = models.get(returning.__name__)
        if existing is not None and existing is not returning:
            raise ModelDeclarationError(
                name=returning.__name__,
                first_module=existing.__module__,
                second_module=returning.__module__,
            )
        models[returning.__name__] = returning
    return models
