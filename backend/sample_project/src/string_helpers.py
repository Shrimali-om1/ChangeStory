"""
Sample project — string helpers.
Used by the bundled 'rename-function' scenario.
"""


def normalise_username(name: str) -> str:
    """Return the username in canonical form."""
    return name.strip().lower()


def truncate(text: str, max_len: int = 80) -> str:
    return text[:max_len]
