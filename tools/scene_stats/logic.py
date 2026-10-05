"""Headless-compatible collection and serialization of scene statistics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


@dataclass
class ImageInfo:
    """Describe the resolution of one image data-block.

    Attributes:
        name: Image data-block name.
        width: Image width in pixels.
        height: Image height in pixels.
    """

    name: str
    width: int
    height: int


@dataclass
class SceneStatsReport:
    """Store a point-in-time report of BlendData statistics.

    Attributes:
        total_objects: Number of object data-blocks.
        objects_by_type: Object counts keyed by ``Object.type``.
        total_polygons: Polygon count across non-evaluated mesh data-blocks.
        mesh_count: Number of mesh data-blocks.
        material_count: Number of material data-blocks.
        collection_count: Number of collection data-blocks.
        image_count: Number of image data-blocks, including unloaded images.
        images: Names and resolutions of images with non-zero dimensions.
        generated_at: UTC ISO 8601 timestamp for report generation.
    """

    total_objects: int
    objects_by_type: dict[str, int]
    total_polygons: int
    mesh_count: int
    material_count: int
    collection_count: int
    image_count: int
    images: list[ImageInfo]
    generated_at: str


def collect_stats(data: bpy.types.BlendData) -> SceneStatsReport:
    """Collect read-only statistics from explicitly supplied Blender data.

    Polygon counts use original mesh data-blocks rather than evaluated
    dependency-graph geometry. Images whose dimensions are both zero remain in
    ``image_count`` but are omitted from the resolution list.

    Args:
        data: Blender data repository to inspect.

    Returns:
        A new scene statistics report.
    """
    objects_by_type: dict[str, int] = {}
    total_objects = 0
    for scene_object in data.objects:
        total_objects += 1
        object_type = scene_object.type
        objects_by_type[object_type] = objects_by_type.get(object_type, 0) + 1

    images: list[ImageInfo] = []
    for image in data.images:
        width = int(image.size[0])
        height = int(image.size[1])
        if width == 0 and height == 0:
            continue
        images.append(ImageInfo(name=image.name, width=width, height=height))

    return SceneStatsReport(
        total_objects=total_objects,
        objects_by_type=dict(sorted(objects_by_type.items())),
        total_polygons=sum(len(mesh.polygons) for mesh in data.meshes),
        mesh_count=len(data.meshes),
        material_count=len(data.materials),
        collection_count=len(data.collections),
        image_count=len(data.images),
        images=images,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def to_json(report: SceneStatsReport) -> str:
    """Serialize a scene statistics report as formatted JSON.

    Args:
        report: Report to serialize.

    Returns:
        UTF-8-compatible JSON text with human-readable indentation.
    """
    return json.dumps(asdict(report), indent=2, ensure_ascii=False)


def _escape_markdown_cell(value: str) -> str:
    """Escape text for safe use in a Markdown table cell.

    Args:
        value: Untrusted text placed into a table cell.

    Returns:
        Text with table separators and line breaks escaped.
    """
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", "")
        .replace("\n", "<br>")
    )


def to_markdown(report: SceneStatsReport) -> str:
    """Serialize a scene statistics report as readable Markdown tables.

    Args:
        report: Report to serialize.

    Returns:
        Markdown containing a summary table and an image-resolution table.
    """
    summary_rows = (
        ("Generated at (UTC)", report.generated_at),
        ("Objects", str(report.total_objects)),
        ("Meshes", str(report.mesh_count)),
        ("Polygons", str(report.total_polygons)),
        ("Materials", str(report.material_count)),
        ("Collections", str(report.collection_count)),
        ("Images", str(report.image_count)),
    )
    lines = [
        "# Scene Statistics",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in summary_rows)

    lines.extend(
        (
            "",
            "## Objects by Type",
            "",
            "| Type | Count |",
            "| --- | ---: |",
        )
    )
    if report.objects_by_type:
        lines.extend(
            f"| {_escape_markdown_cell(object_type)} | {count} |"
            for object_type, count in report.objects_by_type.items()
        )
    else:
        lines.append("| _None_ | 0 |")

    lines.extend(
        (
            "",
            "## Images",
            "",
            "| Name | Width | Height |",
            "| --- | ---: | ---: |",
        )
    )
    if report.images:
        lines.extend(
            f"| {_escape_markdown_cell(image.name)} | {image.width} | "
            f"{image.height} |"
            for image in report.images
        )
    else:
        lines.append("| _None with a known resolution_ | 0 | 0 |")

    return "\n".join(lines)


def write_report(
    report: SceneStatsReport,
    filepath: Path | str,
    fmt: str,
) -> None:
    """Write a report to a UTF-8 JSON or Markdown file.

    Args:
        report: Report to serialize.
        filepath: Destination file path.
        fmt: Output format, either ``"JSON"`` or ``"MARKDOWN"``.

    Raises:
        ValueError: If ``fmt`` is unsupported.
        OSError: If the destination cannot be written.
    """
    serializers = {
        "JSON": to_json,
        "MARKDOWN": to_markdown,
    }
    try:
        serializer = serializers[fmt]
    except KeyError as error:
        raise ValueError(
            f"Unsupported report format {fmt!r}; expected JSON or MARKDOWN"
        ) from error

    Path(filepath).write_text(serializer(report), encoding="utf-8", newline="\n")
