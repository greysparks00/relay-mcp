from tools._store import save


def remember_fact(name: str, fact: str) -> str:
    """Save a user-requested fact or preference in local Relay memory. Reusing a name replaces its value."""
    key = save("fact", name, fact)
    return f"Remembered {key}."
