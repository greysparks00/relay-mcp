from tools._vault import find, parts, vault


# Read the complete Markdown body of one memory by exact name. Supply its category for
# duplicate names.
def read_fact(name: str, category: str | None = None) -> dict[str, str]:
    with vault() as root:
        path = find(root, name, category)
        if path is None:
            raise ValueError("No fact with that name was found.")
        _, body = parts(path.read_bytes())
        return {"name": name.strip(), "category": path.parent.name, "fact": body}
