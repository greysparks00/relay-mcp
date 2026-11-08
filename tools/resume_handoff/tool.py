from tools._vault import HANDOFFS, entry_name, find_named, folder_notes, parts, updated_at, vault


# Read the current Markdown summary of a conversation checkpoint by exact topic.
def resume_handoff(topic: str) -> dict[str, str]:
    key = entry_name(topic)
    with vault() as root:
        path = find_named(folder_notes(root / HANDOFFS), key)
        if path is None:
            raise ValueError("No handoff exists for this topic.")
        _, body = parts(path.read_bytes())
        return {"topic": key, "summary": body.rstrip("\r\n"), "updated_at": updated_at(path)}
