from tools._store import database, entry_name


def resume_handoff(topic: str) -> dict[str, str]:
    """Read a saved Relay conversation checkpoint by its exact topic name."""
    with database() as db:
        row = db.execute("""
            SELECT name AS topic, body AS summary, updated_at FROM entries
            WHERE kind = 'handoff' AND name = ?
        """, (entry_name(topic),)).fetchone()
    if row is None:
        raise ValueError("No handoff exists for this topic.")
    return dict(row)
