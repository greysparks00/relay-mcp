from tools._vault import HANDOFFS, folder_notes, updated_at, vault


# List saved Relay conversation topics, most recently updated first. Use a topic with
# resume_handoff.
def list_handoffs(limit: int = 10, offset: int = 0) -> list[dict[str, str]]:
    if not 1 <= limit <= 50 or offset < 0:
        raise ValueError("Use a limit of 1 to 50 and a nonnegative offset.")
    with vault() as root:
        rows = [{"topic": name, "updated_at": updated_at(path)} for name, path in folder_notes(root / HANDOFFS)]
        rows.sort(key=lambda row: row["topic"].casefold())
        rows.sort(key=lambda row: row["updated_at"], reverse=True)
        return rows[offset:offset + limit]
