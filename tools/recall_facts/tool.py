from tools._vault import notes, parts, vault


def recall_facts(query: str, limit: int = 5, category: str | None = None) -> list[dict[str, str]]:
    """Search memory note names and Markdown bodies. Optionally filter by category. Empty queries list recent memories."""
    if not 1 <= limit <= 10:
        raise ValueError("Limit must be between 1 and 10.")
    needle = query.strip().casefold()
    with vault() as root:
        recent = sorted(notes(root, category), key=lambda item: (-item[1].stat().st_mtime_ns, item[0].casefold()))
        matches = []
        for name, path in recent:
            _, body = parts(path.read_bytes())
            if needle in name.casefold() or needle in body.casefold():
                matches.append({"name": name, "fact": body.rstrip("\r\n"), "category": path.parent.name})
                if len(matches) == limit:
                    break
        return matches
