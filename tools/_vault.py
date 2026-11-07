"""Store each Relay memory as a Markdown file in an Obsidian category folder."""

from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
import json
import ntpath
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from filelock import FileLock
import yaml

CATEGORIES = ("Inbox", "Preferences", "People", "Projects", "Routines", "Reference")
HANDOFFS = "Handoffs"
VAULT_FOLDERS = (*CATEGORIES, HANDOFFS)
PROJECT = Path(__file__).resolve().parents[1]


def entry_name(name: str) -> str:
    key = name.strip().casefold()
    if not 1 <= len(key) <= 100:
        raise ValueError("Use a name between 1 and 100 characters.")
    return key


def updated_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def vault_root() -> Path:
    base = Path(os.environ.get("RELAY_MCP_DATA_DIR") or PROJECT)
    return Path(os.environ.get("RELAY_MCP_VAULT_DIR") or base / "vault").expanduser().resolve()


def category_name(value: str) -> str:
    for category in CATEGORIES:
        if value.strip().casefold() == category.casefold():
            return category
    raise ValueError(f"Choose a category from {', '.join(CATEGORIES)}.")


def require_local(path: Path) -> None:
    if path.is_symlink() or path.is_junction() or path.resolve() != path:
        raise ValueError(f"Linked vault entries are unsupported: {path.name}")


@contextmanager
def vault():
    root = vault_root()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".relay.lock"
    require_local(lock)
    with FileLock(str(lock), timeout=10):
        for name in VAULT_FOLDERS:
            folder = root / name
            require_local(folder)
            folder.mkdir(exist_ok=True)
        yield root


def parts(raw: bytes) -> tuple[str, str]:
    text = raw.decode("utf-8-sig")
    if text.startswith(("---\n", "---\r\n")):
        end = re.search(r"^(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", text[text.index("\n") + 1:], re.M)
        if not end:
            raise ValueError("The note has an unclosed YAML properties block.")
        pos = text.index("\n") + 1 + end.end()
        return text[:pos], text[pos:]
    return "", text


def filename(name: str) -> str:
    # Note names may contain path separators or Windows device names.
    if (name.startswith((".", "~relay-")) or ":" in name or ntpath.isreserved(name)
            or re.search(r'[/\\#\[\]|^]', name) or len(name.encode()) > 200):
        return "~relay-" + sha256(entry_name(name).encode()).hexdigest() + ".md"
    return name + ".md"


def folder_notes(folder: Path):
    for path in folder.iterdir():
        if path.name.startswith(".") or path.suffix.casefold() != ".md":
            continue
        if path.is_symlink() or path.is_junction() or not path.is_file():
            continue
        title = path.stem
        if title.startswith("~relay-"):
            header, _ = parts(path.read_bytes())
            properties = yaml.safe_load("\n".join(header.splitlines()[1:-1]))
            if isinstance(properties, dict) and isinstance(properties.get("relay_name"), str):
                title = properties["relay_name"]
        yield title, path


def notes(root: Path, category: str | None = None):
    folders = (category_name(category),) if category is not None else CATEGORIES
    for folder in folders:
        yield from folder_notes(root / folder)


def find_named(entries, name: str):
    key = entry_name(name)
    matches = [path for title, path in entries if title.casefold() == key]
    if len(matches) > 1:
        raise ValueError("Several notes match this name. Choose a category or rename a duplicate.")
    return matches[0] if matches else None


def find(root: Path, name: str, category: str | None):
    return find_named(notes(root, category), name)


def write_note(path: Path, header: str, body: str, previous: bytes | None) -> None:
    require_local(path)
    if not body.strip():
        raise ValueError("A memory cannot be empty.")
    with NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        if header and not header.endswith("\n"):
            header += "\n"
        encoding = "utf-8-sig" if previous and previous.startswith(b"\xef\xbb\xbf") else "utf-8"
        temporary.write_bytes((header + body).encode(encoding))
        if previous is None:
            # An exclusive link publishes the finished file without replacing a concurrent creation.
            os.link(temporary, path)
        else:
            if path.read_bytes() != previous:
                raise ValueError("The note changed during this operation. Read it again.")
            temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def create_note(folder: Path, name: str, body: str) -> Path:
    title = name.strip()
    entry_name(title)
    path = folder / filename(title)
    header = "---\ntags:\n  - relay/memory\n"
    if path.stem.startswith("~relay-"):
        header += "relay_name: " + json.dumps(title, ensure_ascii=False) + "\n"
    write_note(path, header + "---\n", body, None)
    return path


def save_body(folder: Path, name: str, fact: str, path: Path | None) -> None:
    fact = fact.strip()
    if not 1 <= len(fact) <= 4000:
        raise ValueError("Content must be between 1 and 4000 characters.")
    if path is None:
        create_note(folder, name, fact + "\n")
    else:
        previous = path.read_bytes()
        header, _ = parts(previous)
        write_note(path, header, fact + "\n", previous)


def remember(root: Path, name: str, fact: str, category: str | None) -> None:
    folder = category_name(category) if category is not None else "Inbox"
    save_body(root / folder, name, fact, find(root, name, category))
