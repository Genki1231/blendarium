"""Scene statistics tool implementing the Blendarium tool contract."""

import bpy

from . import ui


TOOL_ID: str = "scene_stats"
TOOL_LABEL: str = "Scene Stats"
TOOL_DESCRIPTION: str = "Collect and export scene statistics"
TOOL_ORDER: int = 20


def register() -> None:
    """Register the Scene Stats tool's operators and panel."""
    for cls in ui.CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the Scene Stats tool's classes in reverse order."""
    for cls in reversed(ui.CLASSES):
        bpy.utils.unregister_class(cls)
