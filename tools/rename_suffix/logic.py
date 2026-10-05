"""Headless-compatible planning and application of object name changes."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import bpy


SUFFIX = "_geo"
NUMBER_WIDTH = 3
FALLBACK_BASE = "object"

_BLENDER_DUPLICATE_PATTERN = re.compile(r"\.\d+$")
_TOOL_SUFFIX_PATTERN = re.compile(r"(_\d+)?_geo$")


@dataclass
class RenameAction:
    """Describe one object name change.

    Attributes:
        original_name: Object name before the rename.
        new_name: Object name after the rename.
    """

    original_name: str
    new_name: str


def compute_base_name(name: str) -> str:
    """Return the stable base used to group an object name.

    A single Blender duplicate suffix is removed first, followed by a single
    suffix pattern owned by this tool.

    Args:
        name: Object name to normalize.

    Returns:
        The normalized base name, or the fallback when normalization is empty.
    """
    base_name = _BLENDER_DUPLICATE_PATTERN.sub("", name, count=1)
    base_name = _TOOL_SUFFIX_PATTERN.sub("", base_name, count=1)
    return base_name or FALLBACK_BASE


def _numbered_name(base_name: str, index: int) -> str:
    """Build one numbered target name.

    Args:
        base_name: Normalized object name shared by a group.
        index: Positive sequence number for the target.

    Returns:
        A target ending in a zero-padded counter and the tool suffix.
    """
    return f"{base_name}_{index:0{NUMBER_WIDTH}d}{SUFFIX}"


def build_rename_plan(
    selected_names: Sequence[str],
    all_names: Iterable[str],
) -> list[RenameAction]:
    """Build an ordered, collision-free rename plan.

    Args:
        selected_names: Selected object names in Blender selection order.
        all_names: Names of every object currently stored in Blender data.

    Returns:
        Required name changes in selection order, excluding no-op changes.
    """
    groups: dict[str, list[str]] = {}
    for original_name in selected_names:
        base_name = compute_base_name(original_name)
        groups.setdefault(base_name, []).append(original_name)

    reserved = set(all_names) - set(selected_names)
    plan: list[RenameAction] = []

    for base_name, group_names in groups.items():
        if len(group_names) == 1:
            original_name = group_names[0]
            candidate = f"{base_name}{SUFFIX}"

            if candidate in reserved:
                candidate_index = 1
                candidate = _numbered_name(base_name, candidate_index)
                while candidate in reserved:
                    candidate_index += 1
                    candidate = _numbered_name(base_name, candidate_index)

            reserved.add(candidate)
            if candidate != original_name:
                plan.append(RenameAction(original_name, candidate))
            continue

        candidate_index = 1
        for original_name in group_names:
            candidate = _numbered_name(base_name, candidate_index)
            while candidate in reserved:
                candidate_index += 1
                candidate = _numbered_name(base_name, candidate_index)

            reserved.add(candidate)
            if candidate != original_name:
                plan.append(RenameAction(original_name, candidate))
            candidate_index += 1

    return plan


def apply_rename_plan(
    objects_by_name: Mapping[str, bpy.types.Object],
    plan: Sequence[RenameAction],
) -> int:
    """Apply a rename plan through collision-safe temporary names.

    Missing source names are ignored. Every available object receives a unique
    temporary name before any final target is assigned.

    Args:
        objects_by_name: Objects keyed by their names before any rename.
        plan: Ordered name changes to apply.

    Returns:
        Number of objects that received their planned final name.
    """
    pending_renames: list[tuple[bpy.types.Object, str]] = []
    temporary_names = set(objects_by_name)
    temporary_names.update(action.new_name for action in plan)

    for action in plan:
        scene_object = objects_by_name.get(action.original_name)
        if scene_object is None:
            continue

        temporary_name = f"__blendarium_tmp_{uuid4().hex}"
        while temporary_name in temporary_names:
            temporary_name = f"__blendarium_tmp_{uuid4().hex}"
        temporary_names.add(temporary_name)

        scene_object.name = temporary_name
        pending_renames.append((scene_object, action.new_name))

    for scene_object, new_name in pending_renames:
        scene_object.name = new_name

    return len(pending_renames)
