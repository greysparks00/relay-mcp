from tools._vault import find, parts, vault


def read_fact(name: str, category: str | None = None) -> dict[str, str]:
    """Read the complete Markdown body of one memory by exact name. Supply its category for duplicate names."""
    with vault() as root:
        path = find(root, name, category)
        if path is None:
            raise ValueError("No fact with that name was found.")
        _, body = parts(path.read_bytes())
        return {"name": name.strip(), "category": path.parent.name, "fact": body}
