from tools._vault import HANDOFFS, entry_name, find_named, folder_notes, save_body, vault


def save_handoff(topic: str, summary: str) -> str:
    """Save decisions, open questions and next steps in a vault handoff note. Reusing a topic replaces its summary."""
    key = entry_name(topic)
    with vault() as root:
        folder = root / HANDOFFS
        save_body(folder, key, summary, find_named(folder_notes(folder), key))
    return f"Saved handoff for {key}."
