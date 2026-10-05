"""Blender UI operators and panel for scene statistics."""

from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from ...core import settings
from . import logic


_last_report: logic.SceneStatsReport | None = None
TOOL_SETTINGS_ID: str = "scene_stats"


def _report_for_export() -> logic.SceneStatsReport:
    """Return the cached report, collecting it when necessary.

    Returns:
        The most recently collected scene statistics report.
    """
    global _last_report
    if _last_report is None:
        _last_report = logic.collect_stats(bpy.data)
    return _last_report


def _export_report(
    operator: bpy.types.Operator,
    filepath: str,
    format_kind: str,
) -> set[str]:
    """Write and persist one export requested by a Blender operator.

    Args:
        operator: Operator used to report completion to the user.
        filepath: File-browser destination path.
        format_kind: Output format accepted by ``logic.write_report``.

    Returns:
        Blender's FINISHED operator status.
    """
    output_path = Path(filepath)
    logic.write_report(_report_for_export(), output_path, format_kind)
    settings.save(TOOL_SETTINGS_ID, {"last_export_format": format_kind})
    operator.report({"INFO"}, f"Scene statistics saved to {output_path}")
    return {"FINISHED"}

class BLENDARIUM_OT_scene_stats_refresh(bpy.types.Operator):
    """Collect current scene statistics and update the UI cache."""

    bl_idname = "blendarium.scene_stats_refresh"
    bl_label = "Refresh"
    bl_description = "Collect current scene statistics"

    def execute(self, _context: bpy.types.Context) -> set[str]:
        """Collect statistics and report completion.

        Args:
            _context: Current Blender context, unused by this operator.

        Returns:
            Blender's FINISHED operator status.
        """
        global _last_report
        _last_report = logic.collect_stats(bpy.data)
        self.report({"INFO"}, "Scene statistics updated")
        return {"FINISHED"}


class BLENDARIUM_OT_scene_stats_export_json(
    bpy.types.Operator,
    ExportHelper,
):
    """Export the cached scene statistics as JSON."""

    bl_idname = "blendarium.scene_stats_export_json"
    bl_label = "Export JSON"
    bl_description = "Export scene statistics as JSON"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, _context: bpy.types.Context) -> set[str]:
        """Write the JSON report selected in the file browser.

        Args:
            _context: Current Blender context, unused by this operator.

        Returns:
            Blender's FINISHED operator status.
        """
        return _export_report(self, self.filepath, "JSON")


class BLENDARIUM_OT_scene_stats_export_markdown(
    bpy.types.Operator,
    ExportHelper,
):
    """Export the cached scene statistics as Markdown."""

    bl_idname = "blendarium.scene_stats_export_markdown"
    bl_label = "Export Markdown"
    bl_description = "Export scene statistics as Markdown"

    filename_ext = ".md"
    filter_glob: StringProperty(default="*.md", options={"HIDDEN"})

    def execute(self, _context: bpy.types.Context) -> set[str]:
        """Write the Markdown report selected in the file browser.

        Args:
            _context: Current Blender context, unused by this operator.

        Returns:
            Blender's FINISHED operator status.
        """
        return _export_report(self, self.filepath, "MARKDOWN")


class BLENDARIUM_PT_scene_stats(bpy.types.Panel):
    """Display scene statistics under the Blendarium shell."""

    bl_label = "Scene Stats"
    bl_idname = "BLENDARIUM_PT_scene_stats"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendarium"
    bl_parent_id = "BLENDARIUM_PT_shell"

    def draw(self, _context: bpy.types.Context) -> None:
        """Draw collection results and export controls.

        Args:
            _context: Current Blender context, unused by this panel.
        """
        layout = self.layout
        layout.operator(BLENDARIUM_OT_scene_stats_refresh.bl_idname)

        if _last_report is None:
            layout.label(text="Press Refresh to collect statistics")
            return

        summary = (
            ("Objects", _last_report.total_objects),
            ("Polygons", _last_report.total_polygons),
            ("Materials", _last_report.material_count),
            ("Collections", _last_report.collection_count),
            ("Images", _last_report.image_count),
        )
        column = layout.column(align=True)
        for label, value in summary:
            row = column.row()
            row.label(text=label)
            row.label(text=str(value))

        export_row = layout.row(align=True)
        export_row.operator(BLENDARIUM_OT_scene_stats_export_json.bl_idname)
        export_row.operator(
            BLENDARIUM_OT_scene_stats_export_markdown.bl_idname
        )


CLASSES: tuple[type, ...] = (
    BLENDARIUM_OT_scene_stats_refresh,
    BLENDARIUM_OT_scene_stats_export_json,
    BLENDARIUM_OT_scene_stats_export_markdown,
    BLENDARIUM_PT_scene_stats,
)
