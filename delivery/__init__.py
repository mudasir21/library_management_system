"""Delivery layer containing CLI and REST API adapters."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from library.delivery.api import app, create_app
    from library.delivery.cli import build_parser, main


def __getattr__(name: str) -> Any:
    """Lazy-load delivery adapters on demand to prevent runpy cycle warnings."""
    if name in ("app", "create_app"):
        from library.delivery import api
        return getattr(api, name)
    if name in ("build_parser", "main"):
        from library.delivery import cli
        return getattr(cli, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["app", "create_app", "build_parser", "main"]
