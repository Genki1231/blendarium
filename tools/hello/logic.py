"""Pure greeting logic for the sample Hello tool."""


def build_greeting(target: str = "Blendarium") -> str:
    """Build a greeting for a named target.

    Args:
        target: Name included in the greeting.

    Returns:
        A human-readable greeting.
    """
    return f"Hello from {target}"
