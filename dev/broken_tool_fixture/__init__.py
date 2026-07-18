"""Deliberately broken package used to verify registry error isolation."""

# Copy this folder into tools/ and start Blender to verify that other tools
# keep working and the shell shows a warning, then delete the copied folder.
raise RuntimeError("Intentional import failure for error-isolation testing")
