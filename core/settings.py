"""Per-tool JSON persistence in Blender's local extension user directory."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import bpy

from . import ROOT_PACKAGE, logger


_LOGGER = logger.get_logger("settings")
_SCHEMA_VERSION = 1


def _validate_tool_id(tool_id: str) -> None:
    """Reject identifiers that could escape the settings directory.

    Args:
        tool_id: Tool identifier used as a settings filename stem.

    Raises:
        TypeError: If ``tool_id`` is not a string.
        ValueError: If the identifier is empty or contains path components.
    """
    if type(tool_id) is not str:
        raise TypeError("tool_id must be str")
    if (
        not tool_id
        or PurePosixPath(tool_id).name != tool_id
        or PureWindowsPath(tool_id).name != tool_id
        or tool_id in {".", ".."}
    ):
        raise ValueError("tool_id must be a single non-empty path component")


def _settings_directory() -> Path:
    """Return the local settings directory created by Blender.

    Returns:
        Path to Blendarium's per-user settings directory.
    """
    return Path(
        bpy.utils.extension_path_user(
            ROOT_PACKAGE,
            path="settings",
            create=True,
        )
    )


def _settings_path(tool_id: str) -> Path:
    """Build a validated settings path for one tool.

    Args:
        tool_id: Tool identifier used as the filename stem.

    Returns:
        Path to ``<tool_id>.json``.
    """
    _validate_tool_id(tool_id)
    return _settings_directory() / f"{tool_id}.json"


def _extract_data(payload: Any) -> dict[str, Any]:
    """Validate a persisted settings envelope and return its data.

    Args:
        payload: JSON-decoded value.

    Returns:
        A shallow copy of the validated data object.

    Raises:
        ValueError: If the JSON envelope does not match schema version 1.
    """
    if type(payload) is not dict:
        raise ValueError("Settings root must be a JSON object")
    if type(payload.get("schema_version")) is not int:
        raise ValueError("schema_version must be an integer")
    if payload["schema_version"] != _SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version: {payload['schema_version']!r}"
        )

    data = payload.get("data")
    if type(data) is not dict:
        raise ValueError("data must be a JSON object")
    return dict(data)


def _quarantine_corrupt_file(settings_path: Path, error: Exception) -> None:
    """Move a corrupt settings file aside without overwriting prior copies.

    Args:
        settings_path: Existing corrupt JSON file.
        error: Parsing or envelope-validation error for the warning log.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    broken_path = settings_path.with_name(
        f"{settings_path.name}.broken-{timestamp}"
    )
    collision_index = 1
    while broken_path.exists():
        broken_path = settings_path.with_name(
            f"{settings_path.name}.broken-{timestamp}-{collision_index}"
        )
        collision_index += 1

    try:
        os.replace(settings_path, broken_path)
    except OSError:
        _LOGGER.warning(
            "Settings for tool %r are corrupt but could not be moved aside: %s",
            settings_path.stem,
            error,
            exc_info=True,
        )
        return

    _LOGGER.warning(
        "Settings for tool %r were corrupt and moved to %s: %s",
        settings_path.stem,
        broken_path.name,
        error,
    )


def load(tool_id: str, defaults: dict[str, Any]) -> dict[str, Any]:
    """Load one tool's settings or return a copy of its defaults.

    Corrupt JSON and invalid version-1 envelopes are moved to a timestamped
    sibling file before defaults are returned.

    Args:
        tool_id: Tool identifier and settings filename stem.
        defaults: Values to copy when no usable settings file exists.

    Returns:
        Persisted data, or a shallow copy of ``defaults``.
    """
    settings_path = _settings_path(tool_id)
    if not settings_path.exists():
        return dict(defaults)

    try:
        with settings_path.open("r", encoding="utf-8") as settings_file:
            payload = json.load(settings_file)
        return _extract_data(payload)
    except (json.JSONDecodeError, UnicodeError, ValueError, TypeError) as error:
        _quarantine_corrupt_file(settings_path, error)
        return dict(defaults)


def save(tool_id: str, data: dict[str, Any]) -> None:
    """Atomically save one tool's settings envelope.

    The temporary file is created in the target directory so ``os.replace``
    does not cross filesystems.

    Args:
        tool_id: Tool identifier and settings filename stem.
        data: JSON-serializable settings object.
    """
    settings_path = _settings_path(tool_id)
    settings_directory = settings_path.parent
    settings_directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "data": data,
    }
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=settings_directory,
            prefix=f".{tool_id}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, settings_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                _LOGGER.warning(
                    "Could not remove temporary settings file %s.",
                    temporary_path.name,
                    exc_info=True,
                )
