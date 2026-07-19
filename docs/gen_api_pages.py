"""Generate static API reference pages for the Blendarium package.

MkDocs executes this script through ``mkdocs-gen-files`` before it builds the
site navigation. The script discovers Python source files and writes virtual
Markdown pages containing mkdocstrings directives. It never imports the
``blendarium`` package, which is essential because Blender's internal ``bpy``
module is not available on the documentation runner.
"""

from collections.abc import Iterator
from pathlib import Path

import mkdocs_gen_files


PACKAGE_NAME = "blendarium"
SOURCE_ROOT = Path(__file__).resolve().parent.parent
API_DIRECTORY = Path("api")

# Only these package trees are part of the public documentation. Keeping this
# allowlist explicit prevents development helpers and future repository scripts
# from being published merely because they use a ``.py`` extension.
DOCUMENTED_SUBPACKAGES = frozenset({"core", "tools", "ui"})
EXCLUDED_DIRECTORY_NAMES = frozenset({"dev", "__pycache__"})
EXCLUDED_ROOT_FILES = frozenset({"dev_loader.py"})


def _has_package_markers(source_path: Path) -> bool:
    """Return whether every directory containing a source file is a package.

    Python treats a directory with an ``__init__.py`` file as a regular package.
    Checking every directory from the module back to the repository root avoids
    documenting loose Python files stored below a non-package directory.

    Args:
        source_path: Absolute path to a candidate Python source file.

    Returns:
        ``True`` when the repository root and every nested parent directory have
        an ``__init__.py`` marker; otherwise, ``False``.
    """

    if not (SOURCE_ROOT / "__init__.py").is_file():
        return False

    current_directory = source_path.parent
    while current_directory != SOURCE_ROOT:
        if not (current_directory / "__init__.py").is_file():
            return False
        current_directory = current_directory.parent

    return True


def _is_documented_source(source_path: Path) -> bool:
    """Return whether a discovered Python file belongs in the API reference.

    The root package initializer is included explicitly. All other files must be
    below ``core``, ``tools``, or ``ui`` and must pass the package-marker check.
    Development-only paths and bytecode-cache directories are rejected before
    the allowlist is evaluated.

    Args:
        source_path: Absolute path returned by the source-tree traversal.

    Returns:
        ``True`` only for source modules that should receive a generated page.
    """

    relative_path = source_path.relative_to(SOURCE_ROOT)

    if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts):
        return False
    if relative_path in {Path(name) for name in EXCLUDED_ROOT_FILES}:
        return False
    if relative_path == Path("__init__.py"):
        return _has_package_markers(source_path)
    if not relative_path.parts or relative_path.parts[0] not in DOCUMENTED_SUBPACKAGES:
        return False

    return _has_package_markers(source_path)


def _iter_module_sources() -> Iterator[Path]:
    """Yield documented Python source files in a deterministic order.

    Sorting by a POSIX-style relative path makes the generated navigation stable
    across Windows development machines and Linux GitHub Actions runners.

    Yields:
        Absolute paths for every included package module.
    """

    candidates = (
        source_path
        for source_path in SOURCE_ROOT.rglob("*.py")
        if _is_documented_source(source_path)
    )
    yield from sorted(
        candidates,
        key=lambda source_path: source_path.relative_to(SOURCE_ROOT).as_posix(),
    )


def _module_parts(source_path: Path) -> tuple[str, ...]:
    """Build the fully qualified import-name parts for a source file.

    An ``__init__.py`` file documents its containing package rather than a
    fictitious ``.__init__`` module. The root initializer therefore maps to the
    single identifier ``blendarium``.

    Args:
        source_path: Absolute path to an included Python source file.

    Returns:
        Components of the fully qualified mkdocstrings identifier.
    """

    relative_module = source_path.relative_to(SOURCE_ROOT).with_suffix("")
    relative_parts = relative_module.parts
    if relative_parts[-1] == "__init__":
        relative_parts = relative_parts[:-1]

    return (PACKAGE_NAME, *relative_parts)


def _documentation_path(source_path: Path) -> Path:
    """Map a source file to its generated Markdown path below ``api``.

    Package initializers become ``index.md`` files. For example,
    ``core/__init__.py`` maps to ``api/core/index.md``, while
    ``core/logger.py`` maps to ``api/core/logger.md``.

    Args:
        source_path: Absolute path to an included Python source file.

    Returns:
        Documentation path relative to MkDocs' ``docs`` directory.
    """

    relative_document = source_path.relative_to(SOURCE_ROOT).with_suffix(".md")
    if source_path.name == "__init__.py":
        relative_document = relative_document.with_name("index.md")

    return API_DIRECTORY / relative_document


def main() -> None:
    """Generate mkdocstrings pages and the literate navigation summary."""

    navigation = mkdocs_gen_files.Nav()

    for source_path in _iter_module_sources():
        module_parts = _module_parts(source_path)
        identifier = ".".join(module_parts)
        document_path = _documentation_path(source_path)
        navigation_path = document_path.relative_to(API_DIRECTORY)

        navigation[module_parts] = navigation_path.as_posix()

        # mkdocs-gen-files stores this page in MkDocs' virtual file collection;
        # it does not write generated API Markdown into the source tree.
        with mkdocs_gen_files.open(document_path, "w") as document_file:
            document_file.write(f"::: {identifier}\n")

        # Edit links on generated pages should point to the real Python sources.
        mkdocs_gen_files.set_edit_path(
            document_path,
            source_path.relative_to(SOURCE_ROOT),
        )

    with mkdocs_gen_files.open(API_DIRECTORY / "SUMMARY.md", "w") as summary_file:
        summary_file.writelines(navigation.build_literate_nav())


main()
