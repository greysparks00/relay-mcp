from tools._vault import find, parts, vault, write_note


# Replace one exact, unique passage in a memory note. Read the note first. Other text and
# properties are preserved.
def edit_fact(name: str, old_text: str, new_text: str, category: str | None = None) -> str:
    if not old_text:
        raise ValueError("Provide the passage to replace.")
    with vault() as root:
        path = find(root, name, category)
        if path is None:
            raise ValueError("No fact with that name was found.")
        previous = path.read_bytes()
        header, body = parts(previous)
        start = body.find(old_text)
        if start < 0 or body.find(old_text, start + 1) >= 0:
            raise ValueError("The passage must match exactly once. Read the note and select a unique passage.")
        updated = body[:start] + new_text + body[start + len(old_text):]
        write_note(path, header, updated, previous)
    return f"Updated {name.strip()}."
