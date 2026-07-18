"""Sample Hello tool implementing the Blendarium tool contract."""

import bpy

from . import ui


TOOL_ID: str = "hello"
TOOL_LABEL: str = "Hello"
TOOL_DESCRIPTION: str = "Report a greeting from Blendarium"
TOOL_ORDER: int = 10


def register() -> None:
    """Register the Hello tool's operator and panel classes."""
    for cls in ui.CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the Hello tool's classes in reverse order."""
    for cls in reversed(ui.CLASSES):
        bpy.utils.unregister_class(cls)
