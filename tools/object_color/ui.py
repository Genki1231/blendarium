"""Blender UI settings, operator, and panel for the Object Color tool."""

import random

import bpy

from . import logic


class BLENDARIUM_PG_object_color(bpy.types.PropertyGroup):
    """Store Object Color settings on the current scene."""

    color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Viewport object color applied to the selection",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.8, 0.8, 0.8, 1.0),
    )
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=(
            (
                "UNIFORM",
                "Uniform",
                "Apply the picked color to every selected object",
            ),
            (
                "RANDOM",
                "Random",
                "Apply a randomized hue to each selected object",
            ),
        ),
        default="UNIFORM",
    )
    random_saturation: bpy.props.FloatProperty(
        name="Saturation",
        description="Saturation used by randomized colors",
        min=0.0,
        max=1.0,
        default=0.7,
    )
    random_value: bpy.props.FloatProperty(
        name="Value",
        description="Value used by randomized colors",
        min=0.0,
        max=1.0,
        default=0.9,
    )


class BLENDARIUM_OT_object_color_apply(bpy.types.Operator):
    """Set viewport object colors on the current selection."""

    bl_idname = "blendarium.object_color_apply"
    bl_label = "Apply Object Color"
    bl_description = "Set the viewport object color of the selected objects"
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
        """Apply the configured color mode to the current selection.

        Args:
            context: Current Blender context.

        Returns:
            Blender's FINISHED operator status.
        """
        settings = context.scene.blendarium_object_color

        if settings.mode == "UNIFORM":
            color = logic.normalize_color(tuple(settings.color))
            result = logic.apply_uniform_color(
                context.selected_objects,
                color,
            )
        else:
            result = logic.apply_random_colors(
                context.selected_objects,
                random.Random(),
                settings.random_saturation,
                settings.random_value,
                settings.color[3],
            )

        if result.applied == 0:
            self.report({"WARNING"}, "No editable objects in selection")
            return {"FINISHED"}

        summary = f"Set object color on {result.applied} object(s)"
        if result.skipped:
            summary += f"; skipped {result.skipped} linked object(s)"
            self.report({"WARNING"}, summary)
        else:
            self.report({"INFO"}, summary)
        return {"FINISHED"}


class BLENDARIUM_PT_object_color(bpy.types.Panel):
    """Display Object Color controls under the Blendarium shell."""

    bl_label = "Object Color"
    bl_idname = "BLENDARIUM_PT_object_color"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendarium"
    bl_parent_id = "BLENDARIUM_PT_shell"

    def draw(self, context: bpy.types.Context) -> None:
        """Draw selection details and object-color controls.

        Args:
            context: Current Blender context.
        """
        layout = self.layout
        settings = context.scene.blendarium_object_color

        layout.label(text=f"Selected objects: {len(context.selected_objects)}")
        layout.prop(settings, "mode", expand=True)
        layout.prop(settings, "color")
        if settings.mode == "RANDOM":
            layout.prop(settings, "random_saturation")
            layout.prop(settings, "random_value")
        layout.operator(BLENDARIUM_OT_object_color_apply.bl_idname)


CLASSES: tuple[type, ...] = (
    BLENDARIUM_PG_object_color,
    BLENDARIUM_OT_object_color_apply,
    BLENDARIUM_PT_object_color,
)


def register_properties() -> None:
    """Register Object Color settings on Blender scenes."""
    bpy.types.Scene.blendarium_object_color = bpy.props.PointerProperty(
        type=BLENDARIUM_PG_object_color,
    )


def unregister_properties() -> None:
    """Remove Object Color settings from Blender scenes when present."""
    if hasattr(bpy.types.Scene, "blendarium_object_color"):
        del bpy.types.Scene.blendarium_object_color
