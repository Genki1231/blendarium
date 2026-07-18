"""Local console and rotating-file logging for Blendarium."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

from . import ROOT_PACKAGE


LOGGER_NAME: Final[str] = "blendarium"
_HANDLER_MARKER: Final[str] = "_blendarium_owned_handler"
_HANDLER_KIND: Final[str] = "_blendarium_handler_kind"
_LEVELS: Final[dict[str, int]] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}
_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _mark_handler(handler: logging.Handler, kind: str) -> None:
    """Mark a handler so it survives module reload detection.

    Args:
        handler: Handler owned by Blendarium.
        kind: Stable handler category used for duplicate detection.
    """
    setattr(handler, _HANDLER_MARKER, True)
    setattr(handler, _HANDLER_KIND, kind)


def _has_handler(root_logger: logging.Logger, kind: str) -> bool:
    """Return whether an owned handler of the requested kind exists.

    Args:
        root_logger: Blendarium's root logger.
        kind: Handler category to find.

    Returns:
        True when a matching owned handler is already attached.
    """
    return any(
        getattr(handler, _HANDLER_MARKER, False)
        and getattr(handler, _HANDLER_KIND, None) == kind
        for handler in root_logger.handlers
    )


def _log_file_path() -> Path:
    """Resolve the extension-local user log file.

    Returns:
        Path to the rotating log file.

    Raises:
        Exception: Propagates Blender import or path lookup failures so setup
            can fall back to console-only logging.
    """
    import bpy

    log_directory = Path(
        bpy.utils.extension_path_user(
            ROOT_PACKAGE,
            path="logs",
            create=True,
        )
    )
    return log_directory / "blendarium.log"


def setup(level_name: str = "INFO") -> logging.Logger:
    """Configure Blendarium logging without adding duplicate handlers.

    File logging is best-effort. If Blender is unavailable or its extension
    user path cannot be resolved, the console handler remains available.

    Args:
        level_name: One of DEBUG, INFO, WARNING, or ERROR.

    Returns:
        The configured Blendarium root logger.
    """
    root_logger = logging.getLogger(LOGGER_NAME)
    root_logger.propagate = False
    formatter = logging.Formatter(_FORMAT)

    if not _has_handler(root_logger, "console"):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        _mark_handler(console_handler, "console")
        root_logger.addHandler(console_handler)

    if not _has_handler(root_logger, "file"):
        try:
            file_handler = RotatingFileHandler(
                _log_file_path(),
                maxBytes=1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
        except Exception:
            root_logger.debug(
                "File logging is unavailable; using console-only logging.",
                exc_info=True,
            )
        else:
            file_handler.setFormatter(formatter)
            _mark_handler(file_handler, "file")
            root_logger.addHandler(file_handler)

    set_level(level_name)
    return root_logger


def set_level(level_name: str) -> None:
    """Set the Blendarium logger and owned handlers to a named level.

    Unknown values fall back to INFO so a malformed saved preference cannot
    disable extension startup.

    Args:
        level_name: Logging level name supplied by preferences.
    """
    normalized_name = level_name.upper()
    level = _LEVELS.get(normalized_name, logging.INFO)
    root_logger = logging.getLogger(LOGGER_NAME)
    root_logger.setLevel(level)

    for handler in root_logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            handler.setLevel(level)


def get_logger(tool_id: str) -> logging.Logger:
    """Return a child logger for a tool or platform component.

    Args:
        tool_id: Tool or component identifier appended to the logger name.

    Returns:
        A child of the ``blendarium`` logger.
    """
    return logging.getLogger(f"{LOGGER_NAME}.{tool_id}")


def shutdown() -> None:
    """Detach and close only the handlers owned by Blendarium."""
    root_logger = logging.getLogger(LOGGER_NAME)

    for handler in tuple(root_logger.handlers):
        if not getattr(handler, _HANDLER_MARKER, False):
            continue

        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            continue
