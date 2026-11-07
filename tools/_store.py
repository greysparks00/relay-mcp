"""Local persistence shared by Relay memory and conversation handoffs."""

from contextlib import closing, contextmanager
import os
from pathlib import Path
import sqlite3


@contextmanager
def database():
    directory = Path(os.environ.get("RELAY_MCP_DATA_DIR") or Path(__file__).resolve().parents[1] / "data")
    directory.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(directory / "relay.sqlite3")) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                body TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (kind, name)
            )
        """)
        yield db


def entry_name(name: str) -> str:
    name = name.strip().casefold()
    if not 1 <= len(name) <= 100:
        raise ValueError("Use a name between 1 and 100 characters.")
    return name


def save(kind: str, name: str, body: str) -> str:
    name = entry_name(name)
    body = body.strip()
    if not 1 <= len(body) <= 4000:
        raise ValueError("Content must be between 1 and 4000 characters.")
    with database() as db:
        db.execute("""
            INSERT INTO entries VALUES (?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            ON CONFLICT(kind, name) DO UPDATE SET
                body = excluded.body, updated_at = excluded.updated_at
        """, (kind, name, body))
    return name
