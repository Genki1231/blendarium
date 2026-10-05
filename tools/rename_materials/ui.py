"""Blender UI operator and panel for the Rename Materials tool."""

import bpy

from . import logic


class BLENDARIUM_OT_rename_materials_apply(bpy.types.Operator):
    """Create missing materials and rename unique selected-object materials."""

    bl_idname = "blendarium.rename_materials_apply"
    bl_label = "Rename Materials"
    bl_description = (
        "Create missing materials and rename every unique material on the "
        "selected objects"
    )
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
        """Create and rename materials for the current selection.

        Args:
            context: Current Blender context.

        Returns:
            Blender's FINISHED operator status.
        """
        processed_objects = 0
        skipped_objects = 0
        created_materials = 0
        renamed_materials = 0
        adjusted_names: list[str] = []

        for scene_object in context.selected_objects:
            if not logic.supports_materials(scene_object):
                skipped_objects += 1
                continue

            processed_objects += 1
            created_materials += logic.fill_missing_materials(
                scene_object,
                bpy.data.materials.new,
            )

            materials = logic.unique_slot_materials(scene_object)
            base_name = logic.strip_suffix(scene_object.name, "_geo")

            for index, material in enumerate(materials, start=1):
                requested_name = logic.build_material_name(
                    base_name,
                    index,
                    len(materials),
                )
                actual_name = logic.rename_material(material, requested_name)
                renamed_materials += 1

                if actual_name != requested_name:
                    adjusted_names.append(
                        f"{scene_object.name}: \"{requested_name}\" became "
                        f"\"{actual_name}\""
                    )

        summary = (
            f"Processed {processed_objects} object(s); "
            f"skipped {skipped_objects} object(s); "
            f"created {created_materials} material(s); "
            f"renamed {renamed_materials} material(s)"
        )

        if adjusted_names:
            summary += ". Blender adjusted: " + "; ".join(adjusted_names)
            self.report({"WARNING"}, summary)
        else:
            self.report({"INFO"}, summary)

        return {"FINISHED"}


class BLENDARIUM_PT_rename_materials(bpy.types.Panel):
    """Display Rename Materials controls under the Blendarium shell."""

    bl_label = "Rename Materials"
    bl_idname = "BLENDARIUM_PT_rename_materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendarium"
    bl_parent_id = "BLENDARIUM_PT_shell"

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the selection count and material-renaming button.

        Args:
            context: Current Blender context.
        """
        layout = self.layout
        layout.label(text=f"Selected objects: {len(context.selected_objects)}")
        layout.operator(BLENDARIUM_OT_rename_materials_apply.bl_idname)


CLASSES: tuple[type, ...] = (
    BLENDARIUM_OT_rename_materials_apply,
    BLENDARIUM_PT_rename_materials,
)
