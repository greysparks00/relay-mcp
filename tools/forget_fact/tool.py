from tools._store import database, entry_name


def forget_fact(name: str) -> str:
    """Delete one saved Relay fact by exact name when the user asks to forget it."""
    key = entry_name(name)
    with database() as db:
        result = db.execute("DELETE FROM entries WHERE kind = 'fact' AND name = ?", (key,))
        return f"Forgot {key}." if result.rowcount else f"No fact named {key}."
