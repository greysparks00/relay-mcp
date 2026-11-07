from tools._store import database


def recall_facts(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Find saved Relay facts by literal text in the name or value. An empty query lists recent facts."""
    if not 1 <= limit <= 10:
        raise ValueError("Limit must be between 1 and 10.")
    needle = query.strip().casefold()
    with database() as db:
        db.create_function("casefold", 1, str.casefold)
        rows = db.execute("""
            SELECT name, body AS fact FROM entries
            WHERE kind = 'fact' AND (instr(name, ?) > 0 OR instr(casefold(body), ?) > 0)
            ORDER BY updated_at DESC, name LIMIT ?
        """, (needle, needle, limit))
        return [dict(row) for row in rows]
