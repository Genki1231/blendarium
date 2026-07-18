"""Blendarium extension entry point."""

from collections.abc import Callable

from . import tools
from .core import logger, prefs, registry
from .ui import shell


_LOGGER = logger.get_logger("lifecycle")


def register() -> None:
    """Register the Blendarium platform and all enabled tools."""
    logger.setup()
    prefs.register()
    shell.register()
    registry.discover_tools(tools)
    prefs.sync_toggles()
    registry.register_tools()


def unregister() -> None:
    """Unregister Blendarium in reverse order, tolerating partial startup."""
    cleanup_steps: tuple[tuple[str, Callable[[], None]], ...] = (
        ("tools", registry.unregister_all),
        ("UI shell", shell.unregister),
        ("preferences", prefs.unregister),
    )

    for label, cleanup in cleanup_steps:
        try:
            cleanup()
        except Exception:
            _LOGGER.exception("Failed to unregister Blendarium %s.", label)

    logger.shutdown()
