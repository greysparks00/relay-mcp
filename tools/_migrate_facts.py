"""Transfer legacy SQLite facts on startup, without overwriting existing notes."""

from datetime import datetime
import os
from pathlib import Path

from tools._store import database
from tools._vault import PROJECT, create_note, find, parts, vault


def migrate_facts() -> None:
    directory = Path(os.environ.get("RELAY_MCP_DATA_DIR") or PROJECT / "data")
    with vault() as root:
        if not (directory / "relay.sqlite3").exists():
            return
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            for row in db.execute("SELECT * FROM entries WHERE kind = 'fact'"):
                name, body = row["name"], row["body"]
                path = find(root, name, "Inbox")
                if path is None:
                    path = create_note(root, "Inbox", name, body + "\n")
                    stamp = datetime.fromisoformat(row["updated_at"]).timestamp()
                    os.utime(path, (stamp, stamp))
                elif parts(path.read_bytes())[1].rstrip("\r\n") != body:
                    raise ValueError(f"Existing Inbox note differs from legacy fact {name!r}. Rename the note and restart.")
            db.execute("DELETE FROM entries WHERE kind = 'fact'")
