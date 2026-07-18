"""Discovers every concrete `pylzt.methods.base.BaseMethod` subclass.

Duplicated technique from `lzt-testnet`'s `src/lzt_testnet/catalog/registry.py` (D-3 in
00-decisions.md) — a 2nd real consumer of the same pattern. Importing `pylzt.methods` alone
does not transitively import every facade submodule (`market_*.py`, `forum_*.py`,
`antipublic_*.py`, ...); those only register on `BaseMethod.__subclasses__()` once their module
has actually executed. We force that by walking the package tree with `pkgutil.walk_packages`
and importing every submodule found, then collecting subclasses recursively (a subclass may
itself be a base for further subclasses) so the result is independent of import order.
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import lru_cache

import pylzt
import pylzt.methods
from pylzt.methods.base import BaseMethod

__all__ = ["collect_base_methods"]


def _import_all_submodules() -> None:
    package = pylzt.methods
    for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}."):
        importlib.import_module(module_info.name)


def _is_concrete(cls: type[BaseMethod]) -> bool:  # type: ignore[type-arg]
    """A concrete endpoint: not `__abstract__`, and not a parametrized `BaseMethod[X]`
    intermediate submodel Pydantic mints for every `class Foo(BaseMethod[Resp])`."""
    if cls is BaseMethod or cls.__dict__.get("__abstract__"):
        return False
    origin = cls.__pydantic_generic_metadata__.get("origin")
    return origin is None


def _walk_subclasses(cls: type[BaseMethod]) -> set[type[BaseMethod]]:  # type: ignore[type-arg]
    found: set[type[BaseMethod]] = set()  # type: ignore[type-arg]
    for subclass in cls.__subclasses__():
        found.add(subclass)
        found |= _walk_subclasses(subclass)
    return found


@lru_cache(maxsize=1)
def collect_base_methods() -> list[type[BaseMethod]]:  # type: ignore[type-arg]
    """Walks `pylzt.methods` via `pkgutil.walk_packages`, returning every concrete
    (non-abstract) `BaseMethod` subclass found. Cached — pylzt's method catalog is fixed
    for the lifetime of the process, so repeated calls (list_methods, get_method_schema,
    describe_api all hit this) shouldn't re-walk ~210 subclasses every time."""
    _ = pylzt  # ensure top-level package import runs before submodule discovery
    _import_all_submodules()
    return [cls for cls in _walk_subclasses(BaseMethod) if _is_concrete(cls)]
