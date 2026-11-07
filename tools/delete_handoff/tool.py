from tools._store import database, entry_name


def delete_handoff(topic: str) -> str:
    """Delete a saved Relay conversation checkpoint by exact topic when the user asks to remove it."""
    key = entry_name(topic)
    with database() as db:
        result = db.execute("DELETE FROM entries WHERE kind = 'handoff' AND name = ?", (key,))
        return f"Deleted handoff for {key}." if result.rowcount else f"No handoff for {key}."
