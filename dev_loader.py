"""Development bootstrap for loading this add-on directly from source.

Blender executes a file passed to `--python` as the standalone `__main__`
module. Running the add-on's `__init__.py` that way gives it no parent package,
so relative imports such as `from . import operators` cannot be resolved.

This bootstrap instead imports the add-on directory as a normal Python package.
"""

import importlib
import sys
from pathlib import Path


def main():
    """Import the source package correctly and register it with Blender."""

    # `resolve()` produces an absolute path and follows symbolic links. This
    # ensures that package discovery uses the add-on's real filesystem location.
    addon_directory = Path(__file__).resolve().parent

    # The package name comes from the folder name rather than being hard-coded.
    # For a folder named `my_first_addon`, this produces `my_first_addon`.
    module_name = addon_directory.name

    # Python must search the directory CONTAINING the package, not the package
    # directory itself. Putting that parent first also gives this development
    # source precedence over another package with the same name.
    parent_directory = str(addon_directory.parent)

    # Remove an existing occurrence before insertion so the parent is guaranteed
    # to occupy the first search position without creating duplicate entries.
    if parent_directory in sys.path:
        sys.path.remove(parent_directory)

    sys.path.insert(0, parent_directory)

    # When this script is run again in the same Blender session, the package may
    # already be imported and registered. Try to unregister that existing state
    # first. If it was only imported but never registered, Blender may raise an
    # exception; reporting and continuing is appropriate for this dev helper.
    existing_module = sys.modules.get(module_name)

    if existing_module is not None:
        try:
            existing_module.unregister()
        except Exception as error:
            print(
                "[dev_loader] Existing package could not be unregistered: "
                f"{error}"
            )

    # Importing by package name gives `__init__.py` a known parent package, so
    # all relative imports work normally. A full submodule-reload system is
    # intentionally unnecessary for this simple fresh-launch workflow.
    addon_module = importlib.import_module(module_name)
    addon_module.register()


if __name__ == "__main__":
    main()
