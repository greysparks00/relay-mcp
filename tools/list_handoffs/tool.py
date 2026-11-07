from tools._store import database


def list_handoffs(limit: int = 10, offset: int = 0) -> list[dict[str, str]]:
    """List saved Relay conversation topics, most recently updated first. Use a topic with resume_handoff."""
    if not 1 <= limit <= 50 or offset < 0 or offset > 2**63 - 1:
        raise ValueError("Use a limit of 1 to 50 and a nonnegative SQLite offset.")
    with database() as db:
        rows = db.execute("""
            SELECT name AS topic, updated_at FROM entries WHERE kind = 'handoff'
            ORDER BY updated_at DESC, name LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(row) for row in rows]
