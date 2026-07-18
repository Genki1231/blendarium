"""Common 3D Viewport sidebar shell for Blendarium tools."""

import bpy

from ..core import registry


class BLENDARIUM_PT_shell(bpy.types.Panel):
    """Root N-panel that owns every enabled Blendarium tool sub-panel."""

    bl_label = "Blendarium"
    bl_idname = "BLENDARIUM_PT_shell"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendarium"

    def draw(self, _context: bpy.types.Context) -> None:
        """Draw only a warning when one or more tools failed.

        Args:
            _context: Current Blender context, unused by this panel.
        """
        failed_count = sum(
            record.state is registry.ToolState.FAILED
            for record in registry.iter_tools()
        )
        if failed_count == 0:
            return

        warning_box = self.layout.box()
        warning_box.alert = True
        warning_box.label(
            text=f"{failed_count} tool(s) failed to load — see Preferences",
            icon="ERROR",
        )


CLASSES: tuple[type, ...] = (BLENDARIUM_PT_shell,)


def register() -> None:
    """Register the common Blendarium UI shell."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the common Blendarium UI shell."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
