"""Headless-compatible assignment of viewport object colors."""

from __future__ import annotations

import colorsys
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


ColorRGBA = tuple[float, float, float, float]


@dataclass
class ApplyResult:
    """Store the result of applying colors to a collection of objects.

    Attributes:
        applied: Number of editable objects that received a color.
        skipped: Number of linked objects left unchanged.
    """

    applied: int
    skipped: int


def normalize_color(values: Sequence[float]) -> ColorRGBA:
    """Validate and clamp an RGBA color to Blender's supported range.

    Args:
        values: Sequence containing red, green, blue, and alpha channels.

    Returns:
        Four color channels clamped to the inclusive range from 0.0 to 1.0.

    Raises:
        ValueError: If the sequence does not contain exactly four values.
    """
    if len(values) != 4:
        raise ValueError("Expected exactly four RGBA color channels")

    return (
        min(max(float(values[0]), 0.0), 1.0),
        min(max(float(values[1]), 0.0), 1.0),
        min(max(float(values[2]), 0.0), 1.0),
        min(max(float(values[3]), 0.0), 1.0),
    )


def is_editable(obj: bpy.types.Object) -> bool:
    """Return whether an object's color can be edited safely.

    Args:
        obj: Blender object to inspect.

    Returns:
        False for linked-library objects, otherwise True.
    """
    return obj.library is None


def random_color(
    rng: random.Random,
    saturation: float,
    value: float,
    alpha: float,
) -> ColorRGBA:
    """Generate a clamped color with a randomized hue.

    Args:
        rng: Random number generator used to choose the hue.
        saturation: Saturation shared by generated colors.
        value: Value shared by generated colors.
        alpha: Alpha channel shared by generated colors.

    Returns:
        A normalized RGBA color with a random hue.
    """
    red, green, blue = colorsys.hsv_to_rgb(
        rng.random(),
        saturation,
        value,
    )
    return normalize_color((red, green, blue, alpha))


def apply_uniform_color(
    objects: Iterable[bpy.types.Object],
    color: ColorRGBA,
) -> ApplyResult:
    """Assign one normalized color to every editable object.

    Args:
        objects: Blender objects to process.
        color: RGBA color to assign to each editable object.

    Returns:
        Counts of objects that were updated or skipped.
    """
    normalized_color = normalize_color(color)
    applied = 0
    skipped = 0

    for scene_object in objects:
        if not is_editable(scene_object):
            skipped += 1
            continue
        scene_object.color = normalized_color
        applied += 1

    return ApplyResult(applied=applied, skipped=skipped)


def apply_random_colors(
    objects: Iterable[bpy.types.Object],
    rng: random.Random,
    saturation: float,
    value: float,
    alpha: float,
) -> ApplyResult:
    """Assign an independently randomized hue to every editable object.

    Args:
        objects: Blender objects to process.
        rng: Random number generator used to choose each hue.
        saturation: Saturation shared by generated colors.
        value: Value shared by generated colors.
        alpha: Alpha channel shared by generated colors.

    Returns:
        Counts of objects that were updated or skipped.
    """
    applied = 0
    skipped = 0

    for scene_object in objects:
        if not is_editable(scene_object):
            skipped += 1
            continue
        scene_object.color = random_color(
            rng,
            saturation,
            value,
            alpha,
        )
        applied += 1

    return ApplyResult(applied=applied, skipped=skipped)
