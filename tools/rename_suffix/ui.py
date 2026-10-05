"""Blender UI operator and panel for the Rename Suffix tool."""

import bpy

from . import logic


class BLENDARIUM_OT_rename_suffix_apply(bpy.types.Operator):
    """Append the geometry suffix to selected object names."""

    bl_idname = "blendarium.rename_suffix_apply"
    bl_label = "Add _geo Suffix"
    bl_description = "Append the _geo suffix to selected object names"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(
        cls,
        context: bpy.types.Context,
    ) -> bool:
        """Return whether at least one object is selected.

        Args:
            cls: Operator class being polled.
            context: Current Blender context.

        Returns:
            True when the context has one or more selected objects.
        """
        return bool(context.selected_objects)

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Build and apply a rename plan for the current selection.

        Args:
            context: Current Blender context.

        Returns:
            Blender's FINISHED operator status.
        """
        selected_objects = list(context.selected_objects)
        selected_names = [
            scene_object.name for scene_object in selected_objects
        ]
        all_names = [scene_object.name for scene_object in bpy.data.objects]
        objects_by_name = {
            scene_object.name: scene_object
            for scene_object in selected_objects
        }

        plan = logic.build_rename_plan(selected_names, all_names)
        renamed_count = logic.apply_rename_plan(objects_by_name, plan)

        if renamed_count == 0:
            self.report({"INFO"}, "No objects needed renaming")
        else:
            self.report({"INFO"}, f"Renamed {renamed_count} object(s)")
        return {"FINISHED"}


class BLENDARIUM_PT_rename_suffix(bpy.types.Panel):
    """Display Rename Suffix controls under the Blendarium shell."""

    bl_label = "Rename Suffix"
    bl_idname = "BLENDARIUM_PT_rename_suffix"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendarium"
    bl_parent_id = "BLENDARIUM_PT_shell"

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the selection count and rename button.

        Args:
            context: Current Blender context.
        """
        layout = self.layout
        layout.label(text=f"Selected objects: {len(context.selected_objects)}")
        layout.operator(BLENDARIUM_OT_rename_suffix_apply.bl_idname)


CLASSES: tuple[type, ...] = (
    BLENDARIUM_OT_rename_suffix_apply,
    BLENDARIUM_PT_rename_suffix,
)
