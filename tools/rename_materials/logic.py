"""Headless-compatible naming and material-slot helpers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import bpy


class MaterialFactory(Protocol):
    """Describe the Blender callable used to create a material data-block."""

    def __call__(self, *, name: str) -> bpy.types.Material:
        """Create a material with the requested initial name.

        Args:
            name: Initial name requested for the material data-block.

        Returns:
            The newly created material.
        """
        ...


def strip_suffix(name: str, suffix: str = "_geo") -> str:
    """Remove a suffix only when it appears at the end of a name.

    Matching is case-insensitive, and the suffix is treated as literal text.

    Args:
        name: Name to inspect.
        suffix: Literal suffix to remove.

    Returns:
        The name without one matching trailing suffix.
    """
    pattern = rf"{re.escape(suffix)}$"
    return re.sub(pattern, "", name, flags=re.IGNORECASE)


def build_material_name(base_name: str, index: int, total: int) -> str:
    """Build a material name for a one-based slot-order index.

    Args:
        base_name: Object-derived name shared by the object's materials.
        index: One-based position among the object's unique materials.
        total: Total number of unique materials on the object.

    Returns:
        An unnumbered name for one material, otherwise a zero-padded name.
    """
    if total == 1:
        return f"{base_name}_mat"
    return f"{base_name}_{index:03d}_mat"


def supports_materials(obj: bpy.types.Object) -> bool:
    """Return whether an object's data block exposes materials.

    Args:
        obj: Blender object to inspect.

    Returns:
        True when the object has a data block with a materials collection.
    """
    return obj.data is not None and hasattr(obj.data, "materials")


def fill_missing_materials(
    obj: bpy.types.Object,
    material_factory: MaterialFactory,
) -> int:
    """Create a distinct material for every missing material slot.

    An object with no slots first receives a material through its data block,
    which creates the initial slot. Every remaining empty slot then receives a
    separate new material.

    Args:
        obj: Blender object whose material slots should be populated.
        material_factory: Callable equivalent to ``bpy.data.materials.new``.

    Returns:
        Number of material data-blocks created.
    """
    created_count = 0

    if len(obj.material_slots) == 0:
        material = material_factory(name="Material")
        obj.data.materials.append(material)
        created_count += 1

    for slot in obj.material_slots:
        if slot.material is None:
            material = material_factory(name="Material")
            slot.material = material
            created_count += 1

    return created_count


def unique_slot_materials(
    obj: bpy.types.Object,
) -> list[bpy.types.Material]:
    """Collect unique non-empty slot materials in first-appearance order.

    List membership is deliberate so repeated references to the same Blender
    material contribute only once while preserving slot order.

    Args:
        obj: Blender object whose material slots should be inspected.

    Returns:
        Unique non-None materials in first-slot order.
    """
    unique_materials: list[bpy.types.Material] = []

    for slot in obj.material_slots:
        material = slot.material
        if material is not None and material not in unique_materials:
            unique_materials.append(material)

    return unique_materials


def rename_material(material: bpy.types.Material, new_name: str) -> str:
    """Rename a material and return the name Blender actually assigned.

    Args:
        material: Material data-block to rename.
        new_name: Requested material name.

    Returns:
        Material name after Blender applies uniqueness rules.
    """
    material.name = new_name
    return material.name
