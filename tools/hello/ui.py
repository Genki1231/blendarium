"""Blender UI classes for the sample Hello tool."""

import bpy

from .logic import build_greeting


class BLENDARIUM_OT_hello(bpy.types.Operator):
    """Report a greeting through Blender's status interface."""

    bl_idname = "blendarium.hello"
    bl_label = "Say Hello"
    bl_description = "Report a greeting from Blendarium"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> set[str]:
        """Report the greeting and complete the operator.

        Args:
            _context: Current Blender context, unused by this operator.

        Returns:
            Blender's FINISHED operator status.
        """
        self.report({"INFO"}, build_greeting())
        return {"FINISHED"}


class BLENDARIUM_PT_hello(bpy.types.Panel):
    """Display the sample Hello action under the Blendarium shell."""

    bl_label = "Hello"
    bl_idname = "BLENDARIUM_PT_hello"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendarium"
    bl_parent_id = "BLENDARIUM_PT_shell"

    def draw(self, _context: bpy.types.Context) -> None:
        """Draw the Hello operator button.

        Args:
            _context: Current Blender context, unused by this panel.
        """
        self.layout.operator(BLENDARIUM_OT_hello.bl_idname)


CLASSES: tuple[type, ...] = (
    BLENDARIUM_OT_hello,
    BLENDARIUM_PT_hello,
)
