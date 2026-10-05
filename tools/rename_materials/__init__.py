"""Material renaming tool implementing the Blendarium tool contract."""

import bpy

from . import ui


TOOL_ID: str = "rename_materials"
TOOL_LABEL: str = "Rename Materials"
TOOL_DESCRIPTION: str = (
    "Create missing materials and rename them from object names"
)
TOOL_ORDER: int = 40


def register() -> None:
    """Register the Rename Materials tool's operator and panel."""
    for cls in ui.CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the Rename Materials tool's classes in reverse order."""
    for cls in reversed(ui.CLASSES):
        bpy.utils.unregister_class(cls)
