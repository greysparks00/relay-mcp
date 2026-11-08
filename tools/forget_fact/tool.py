from tools._vault import find, vault


# Delete a memory note by exact name when the user asks to forget it. Supply its category
# for duplicate names.
def forget_fact(name: str, category: str | None = None) -> str:
    with vault() as root:
        path = find(root, name, category)
        if path is None:
            return f"No fact named {name}."
        path.unlink()
    return f"Forgot {name}."
