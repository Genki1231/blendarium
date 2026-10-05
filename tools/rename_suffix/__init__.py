"""Batch renaming tool implementing the Blendarium tool contract."""

import bpy

from . import ui


TOOL_ID: str = "rename_suffix"
TOOL_LABEL: str = "Rename Suffix"
TOOL_DESCRIPTION: str = "Batch-append the _geo suffix to selected object names"
TOOL_ORDER: int = 30


def register() -> None:
    """Register the Rename Suffix tool's operator and panel."""
    for cls in ui.CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the Rename Suffix tool's classes in reverse order."""
    for cls in reversed(ui.CLASSES):
        bpy.utils.unregister_class(cls)
