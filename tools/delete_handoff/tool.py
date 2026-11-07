from tools._vault import HANDOFFS, entry_name, find_named, folder_notes, vault


def delete_handoff(topic: str) -> str:
    """Delete a saved Relay conversation checkpoint by exact topic when the user asks to remove it."""
    key = entry_name(topic)
    with vault() as root:
        path = find_named(folder_notes(root / HANDOFFS), key)
        if path is None:
            return f"No handoff for {key}."
        path.unlink()
    return f"Deleted handoff for {key}."
