"""Run the Scene Stats logic from Blender without registering the package UI.

Usage:
    blender -b <file.blend> --python dev/run_scene_stats.py -- \
        --output <path.json> [--format JSON|MARKDOWN]
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from types import ModuleType

import bpy


def _arguments_after_separator(argv: list[str]) -> list[str]:
    """Return only command-line arguments following Blender's ``--`` marker.

    Args:
        argv: Complete process argument list.

    Returns:
        Arguments intended for this script, or an empty list when no separator
        is present.
    """
    try:
        separator_index = argv.index("--")
    except ValueError:
        return []
    return argv[separator_index + 1 :]


def _parse_arguments(argv: list[str]) -> argparse.Namespace:
    """Parse supported arguments after Blender's separator.

    Args:
        argv: Complete process argument list.

    Returns:
        Namespace containing the output path and report format.
    """
    parser = argparse.ArgumentParser(
        description="Collect and export Blendarium scene statistics."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scene_stats_output.json"),
        help="Destination report path (default: scene_stats_output.json).",
    )
    parser.add_argument(
        "--format",
        choices=("JSON", "MARKDOWN"),
        default="JSON",
        help="Report format (default: JSON).",
    )
    return parser.parse_args(_arguments_after_separator(argv))


def _import_scene_stats_logic() -> ModuleType:
    """Import Scene Stats logic through the source package's real name.

    Returns:
        Imported ``tools.scene_stats.logic`` module.
    """
    package_directory = Path(__file__).resolve().parents[1]
    package_name = package_directory.name
    parent_directory = str(package_directory.parent)

    if parent_directory in sys.path:
        sys.path.remove(parent_directory)
    sys.path.insert(0, parent_directory)

    importlib.import_module(package_name)
    return importlib.import_module(
        f"{package_name}.tools.scene_stats.logic"
    )


def main() -> None:
    """Collect Blender data statistics and write the requested report."""
    arguments = _parse_arguments(sys.argv)
    scene_stats_logic = _import_scene_stats_logic()
    scene_stats_report = scene_stats_logic.collect_stats(bpy.data)
    scene_stats_logic.write_report(
        scene_stats_report,
        arguments.output,
        arguments.format,
    )
    print(f"SCENE-STATS-OK: {arguments.output}")


if __name__ == "__main__":
    main()
