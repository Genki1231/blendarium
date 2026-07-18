"""Tool discovery, contract validation, and registration isolation."""

import importlib
import pkgutil
import traceback
from dataclasses import dataclass
from enum import Enum, auto
from types import ModuleType
from typing import Any

from . import logger


_LOGGER = logger.get_logger("registry")


class ToolState(Enum):
    """Lifecycle states for a discovered Blendarium tool."""

    DISCOVERED = auto()
    REGISTERED = auto()
    DISABLED = auto()
    FAILED = auto()


@dataclass
class ToolRecord:
    """Store metadata and runtime state for one tool package.

    Attributes:
        tool_id: Folder name and validated tool identifier.
        label: Display label, falling back to ``tool_id`` on failure.
        order: Ascending registration and display order.
        state: Current lifecycle state.
        module: Imported tool module, or None when import failed.
        error: Formatted traceback for a failed tool, otherwise None.
    """

    tool_id: str
    label: str
    order: int
    state: ToolState
    module: ModuleType | None
    error: str | None


_tool_records: dict[str, ToolRecord] = {}
_registration_order: list[str] = []


def _validate_attribute(
    module: ModuleType,
    attribute_name: str,
    expected_type: type,
) -> Any:
    """Return a strictly typed tool contract attribute.

    Args:
        module: Imported tool package.
        attribute_name: Required module-level attribute.
        expected_type: Exact required Python type.

    Returns:
        The validated attribute value.

    Raises:
        AttributeError: If the attribute is missing.
        TypeError: If the attribute has the wrong type.
    """
    if not hasattr(module, attribute_name):
        raise AttributeError(f"Missing required attribute: {attribute_name}")

    value = getattr(module, attribute_name)
    if type(value) is not expected_type:
        raise TypeError(
            f"{attribute_name} must be {expected_type.__name__}, "
            f"not {type(value).__name__}"
        )
    return value


def _validate_contract(module: ModuleType, folder_name: str) -> tuple[str, int]:
    """Validate a tool package's module-level contract.

    Args:
        module: Imported tool package.
        folder_name: Package folder discovered by ``pkgutil``.

    Returns:
        A tuple containing the validated label and order.

    Raises:
        AttributeError: If a required attribute is absent.
        TypeError: If metadata types or callbacks are invalid.
        ValueError: If TOOL_ID differs from the package folder name.
    """
    tool_id = _validate_attribute(module, "TOOL_ID", str)
    label = _validate_attribute(module, "TOOL_LABEL", str)
    _validate_attribute(module, "TOOL_DESCRIPTION", str)
    order = _validate_attribute(module, "TOOL_ORDER", int)

    if tool_id != folder_name:
        raise ValueError(
            f"TOOL_ID must match folder name {folder_name!r}, got {tool_id!r}"
        )

    for callback_name in ("register", "unregister"):
        if not hasattr(module, callback_name):
            raise AttributeError(f"Missing required attribute: {callback_name}")
        if not callable(getattr(module, callback_name)):
            raise TypeError(f"{callback_name} must be callable")

    return label, order


def _record_failure(record: ToolRecord, action: str) -> None:
    """Mark one tool as failed using the active exception traceback.

    Args:
        record: Tool record that encountered an exception.
        action: Short description of the failed lifecycle action.
    """
    record.state = ToolState.FAILED
    record.error = traceback.format_exc()
    _LOGGER.error(
        "Tool %r failed during %s.\n%s",
        record.tool_id,
        action,
        record.error,
    )


def discover_tools(package: ModuleType) -> list[ToolRecord]:
    """Discover, import, and validate direct tool subpackages.

    Package enumeration is completed before any discovered tool is imported.
    Each subsequent import and contract check is isolated from every other
    tool.

    Args:
        package: The ``tools`` package whose ``__path__`` should be scanned.

    Returns:
        All tool records sorted by ``(order, tool_id)``.

    Raises:
        TypeError: If ``package`` does not expose a package search path.
    """
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise TypeError("Tool discovery requires a package with __path__")

    discovered_names = sorted(
        {
            module_info.name
            for module_info in pkgutil.iter_modules(package_path)
            if module_info.ispkg
        }
    )

    _tool_records.clear()
    _registration_order.clear()

    for folder_name in discovered_names:
        _tool_records[folder_name] = ToolRecord(
            tool_id=folder_name,
            label=folder_name,
            order=0,
            state=ToolState.DISCOVERED,
            module=None,
            error=None,
        )

    for folder_name in discovered_names:
        record = _tool_records[folder_name]
        try:
            module = importlib.import_module(f"{package.__name__}.{folder_name}")
            record.module = module
            label, order = _validate_contract(module, folder_name)
        except Exception:
            _record_failure(record, "import or contract validation")
            continue

        record.label = label
        record.order = order

    return iter_tools()


def _is_tool_enabled(tool_id: str) -> bool:
    """Read a tool's enabled preference, defaulting to enabled.

    Args:
        tool_id: Tool identifier to look up.

    Returns:
        The saved enabled state, or True before preferences are available.
    """
    from . import prefs

    return prefs.is_tool_enabled(tool_id)


def _register_record(record: ToolRecord) -> None:
    """Register one validated tool with exception isolation.

    Args:
        record: Tool record to register.
    """
    if record.module is None:
        record.state = ToolState.FAILED
        record.error = "Tool module is unavailable."
        return

    try:
        record.module.register()
    except Exception:
        _record_failure(record, "registration")
        return

    record.state = ToolState.REGISTERED
    record.error = None
    if record.tool_id not in _registration_order:
        _registration_order.append(record.tool_id)


def register_tools() -> None:
    """Register all enabled, valid tools in configured order."""
    for record in iter_tools():
        if record.state in {ToolState.FAILED, ToolState.REGISTERED}:
            continue

        if not _is_tool_enabled(record.tool_id):
            record.state = ToolState.DISABLED
            continue

        _register_record(record)


def _unregister_record(record: ToolRecord, next_state: ToolState) -> bool:
    """Unregister one tool while preserving failure diagnostics.

    Args:
        record: Previously registered tool.
        next_state: State to apply after successful unregistration.

    Returns:
        True when the tool unregistered successfully.
    """
    if record.module is None:
        record.state = ToolState.FAILED
        record.error = "Tool module is unavailable."
        return False

    try:
        record.module.unregister()
    except Exception:
        _record_failure(record, "unregistration")
        return False

    record.state = next_state
    record.error = None
    if record.tool_id in _registration_order:
        _registration_order.remove(record.tool_id)
    return True


def unregister_all() -> None:
    """Unregister tools in reverse registration order and continue on errors."""
    registered_ids = tuple(reversed(_registration_order))

    for tool_id in registered_ids:
        record = _tool_records.get(tool_id)
        if record is None:
            continue
        _unregister_record(record, ToolState.DISCOVERED)

    _registration_order.clear()


def set_tool_enabled(tool_id: str, enabled: bool) -> None:
    """Register or unregister only the requested tool.

    Args:
        tool_id: Identifier stored in the preferences collection entry.
        enabled: Whether the tool should be registered.
    """
    record = _tool_records.get(tool_id)
    if record is None:
        _LOGGER.warning("Ignoring toggle for unknown tool %r.", tool_id)
        return

    if record.state is ToolState.FAILED:
        return

    if enabled:
        if record.state is not ToolState.REGISTERED:
            _register_record(record)
        return

    if record.state is ToolState.REGISTERED:
        _unregister_record(record, ToolState.DISABLED)
    else:
        record.state = ToolState.DISABLED


def iter_tools() -> list[ToolRecord]:
    """Return all tool records sorted by order and identifier.

    Returns:
        A new sorted list that includes failed tools.
    """
    return sorted(
        _tool_records.values(),
        key=lambda record: (record.order, record.tool_id),
    )
