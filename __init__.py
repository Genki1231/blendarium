# Blendarium - a minimal Blender Extension template.
#
# This add-on uses the modern "Extension" format (Blender 4.2+). All metadata
# (name, version, license, ...) lives in `blender_manifest.toml`, so there is
# intentionally NO `bl_info` dictionary here. Adding one would make Blender emit
# a warning when the extension is loaded.
#
# The example below demonstrates the three building blocks every add-on needs:
#   1. An Operator  - a single action the user can run (here: report "Hello").
#   2. A Panel       - a UI box that hosts buttons/fields (here: in the N-panel).
#   3. register / unregister - hooks Blender calls when the add-on is
#      enabled / disabled, used to (de)register the classes above.

import bpy


class BLENDARIUM_OT_hello(bpy.types.Operator):
    """Operator: print a greeting to the status bar when clicked."""

    # `bl_idname` is the unique ID used to call this operator, e.g.
    # bpy.ops.blendarium.hello() or layout.operator("blendarium.hello").
    bl_idname = "blendarium.hello"
    # `bl_label` is the text shown on the button in the UI.
    bl_label = "Say Hello"
    # `bl_description` is the tooltip shown on hover.
    bl_description = "Report a hello message to the status bar"
    # `bl_options` = {'REGISTER', 'UNDO'} makes the action appear in the info
    # log and become undoable with Ctrl+Z.
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # `self.report` shows a message in the status bar / info log.
        # {'INFO'} is the message type (blue). Others: {'WARNING'}, {'ERROR'}.
        self.report({'INFO'}, "Hello from Blendarium")
        # Operators must return a set. {'FINISHED'} means "ran successfully".
        return {'FINISHED'}


class BLENDARIUM_PT_panel(bpy.types.Panel):
    """Panel: shown in the 3D Viewport N-panel under the 'Blendarium' tab."""

    bl_label = "Blendarium"          # Header text of the panel.
    bl_idname = "BLENDARIUM_PT_panel"       # Unique ID for this panel.
    bl_space_type = 'VIEW_3D'            # Show it in the 3D Viewport.
    bl_region_type = 'UI'               # 'UI' = the N-panel (press N to toggle).
    bl_category = "Blendarium"            # Tab name in the N-panel sidebar.

    def draw(self, context):
        # `self.layout` is the container we add UI elements to.
        layout = self.layout
        # Draw a button that runs our operator when clicked.
        layout.operator("blendarium.hello")


# All classes that must be (un)registered with Blender. Add new operators or
# panels here so register()/unregister() pick them up automatically.
classes = (
    BLENDARIUM_OT_hello,
    BLENDARIUM_PT_panel,
)


def register():
    # Called when the add-on is enabled. Register each class with Blender.
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # Called when the add-on is disabled. Unregister in reverse order so that
    # classes are removed before anything that may depend on them.
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
