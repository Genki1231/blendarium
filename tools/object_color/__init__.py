"""Object color tool implementing the Blendarium tool contract."""

import bpy

from . import ui


TOOL_ID: str = "object_color"
TOOL_LABEL: str = "Object Color"
TOOL_DESCRIPTION: str = (
    "Batch-set the viewport object color of selected objects"
)
TOOL_ORDER: int = 50


def register() -> None:
    """Register the Object Color tool's classes and properties."""
    for cls in ui.CLASSES:
        bpy.utils.register_class(cls)
    ui.register_properties()


def unregister() -> None:
    """Unregister the Object Color tool's properties and classes."""
    ui.unregister_properties()
    for cls in reversed(ui.CLASSES):
        bpy.utils.unregister_class(cls)
