"""Blender preferences for Blendarium platform settings."""

from typing import cast

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty

from . import ROOT_PACKAGE, logger, registry


_LOGGER = logger.get_logger("preferences")
_syncing_toggles = False


def _on_tool_toggle(self: "ToolToggle", _context: bpy.types.Context) -> None:
    """Apply a user-initiated tool enablement change immediately.

    Args:
        self: Collection entry whose value changed.
        _context: Blender callback context, unused by this callback.
    """
    if _syncing_toggles:
        return
    registry.set_tool_enabled(self.name, self.enabled)


def _on_log_level_change(
    self: "BlendariumPreferences",
    _context: bpy.types.Context,
) -> None:
    """Apply the selected logging level immediately.

    Args:
        self: Blendarium preferences instance.
        _context: Blender callback context, unused by this callback.
    """
    logger.set_level(self.log_level)


class ToolToggle(bpy.types.PropertyGroup):
    """Store one tool's enabled state using the built-in name as its ID."""

    enabled: BoolProperty(
        name="Enabled",
        description="Enable this Blendarium tool",
        default=True,
        update=_on_tool_toggle,
    )


class BlendariumPreferences(bpy.types.AddonPreferences):
    """Expose Blendarium-wide tool and logging preferences."""

    bl_idname = ROOT_PACKAGE

    tool_toggles: CollectionProperty(type=ToolToggle)
    log_level: EnumProperty(
        name="Log Level",
        description="Minimum severity written to Blendarium logs",
        items=(
            ("DEBUG", "Debug", "Include detailed diagnostic messages"),
            ("INFO", "Info", "Include normal status messages"),
            ("WARNING", "Warning", "Include warnings and errors only"),
            ("ERROR", "Error", "Include errors only"),
        ),
        default="INFO",
        update=_on_log_level_change,
    )

    def draw(self, _context: bpy.types.Context) -> None:
        """Draw tool toggles and the shared log-level setting.

        Args:
            _context: Current Blender context, unused by this panel.
        """
        layout = self.layout
        layout.label(text="Tools")

        for record in registry.iter_tools():
            toggle = self.tool_toggles.get(record.tool_id)
            row = layout.row(align=True)

            if record.state is registry.ToolState.FAILED:
                row.enabled = False
                row.label(text=record.label, icon="ERROR")
                row.label(text="Failed to load")
            else:
                row.label(text=record.label)

            if toggle is not None:
                row.prop(toggle, "enabled", text="")

        layout.separator()
        layout.prop(self, "log_level")


CLASSES: tuple[type, ...] = (
    ToolToggle,
    BlendariumPreferences,
)


def get_preferences() -> BlendariumPreferences | None:
    """Return the active Blendarium preferences instance when available.

    Returns:
        Registered preferences, or None during startup and teardown edges.
    """
    try:
        addon = bpy.context.preferences.addons.get(ROOT_PACKAGE)
    except (AttributeError, RuntimeError):
        return None

    if addon is None:
        return None
    return cast(BlendariumPreferences, addon.preferences)


def is_tool_enabled(tool_id: str) -> bool:
    """Return a tool toggle value, defaulting new tools to enabled.

    Args:
        tool_id: Tool identifier to find in the preferences collection.

    Returns:
        The stored toggle, or True when no entry exists yet.
    """
    preferences = get_preferences()
    if preferences is None:
        return True

    toggle = preferences.tool_toggles.get(tool_id)
    if toggle is None:
        return True
    return bool(toggle.enabled)


def sync_toggles() -> None:
    """Add default-on entries for newly discovered tools.

    Existing and stale entries are deliberately left unchanged. The callback
    guard prevents programmatic initialization from registering tools early.
    """
    global _syncing_toggles

    preferences = get_preferences()
    if preferences is None:
        _LOGGER.warning("Blendarium preferences are unavailable during sync.")
        return

    _syncing_toggles = True
    try:
        for record in registry.iter_tools():
            if preferences.tool_toggles.get(record.tool_id) is not None:
                continue

            toggle = preferences.tool_toggles.add()
            toggle.name = record.tool_id
            toggle.enabled = True
    finally:
        _syncing_toggles = False


def register() -> None:
    """Register preference classes and apply the persisted log level."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    preferences = get_preferences()
    if preferences is not None:
        logger.set_level(preferences.log_level)


def unregister() -> None:
    """Unregister preference classes in reverse dependency order."""
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            _LOGGER.exception("Failed to unregister preference class %s.", cls.__name__)
