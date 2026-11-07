from typing import Literal

from tools._vault import remember, vault


def remember_fact(name: str, fact: str, category: Literal["Inbox", "Preferences", "People", "Projects", "Routines", "Reference"] | None = None) -> str:
    """Save or replace a named Markdown memory. Without a category, update its existing note or create it in Inbox."""
    with vault() as root:
        remember(root, name, fact, category)
    return f"Remembered {name.strip()}."
