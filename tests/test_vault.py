import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from tools._migrate_facts import migrate_facts
from tools._store import database, save
from tools.edit_fact.tool import edit_fact
from tools.forget_fact.tool import forget_fact
from tools.read_fact.tool import read_fact
from tools.recall_facts.tool import recall_facts
from tools.remember_fact.tool import remember_fact


class VaultTests(TestCase):
    def setUp(self):
        temp = self.enterContext(TemporaryDirectory())
        self.root = Path(temp) / "vault"
        self.enterContext(patch.dict(os.environ, {
            "RELAY_MCP_DATA_DIR": temp, "RELAY_MCP_VAULT_DIR": str(self.root)
        }))

    def test_migration_preserves_legacy_keys_and_does_not_restore_forgotten_facts(self):
        save("fact", "../CON", "Original")
        save("handoff", "next", "Keep this")
        migrate_facts()
        self.assertEqual(read_fact("../CON")["fact"].strip(), "Original")
        self.assertEqual(len(list((self.root / "Inbox").glob("*.md"))), 1)
        forget_fact("../CON")
        migrate_facts()
        self.assertEqual(recall_facts(""), [])
        with database() as db:
            self.assertEqual(db.execute("SELECT body FROM entries").fetchone()[0], "Keep this")

    def test_conflicting_migration_is_recoverable(self):
        remember_fact("existing", "New version")
        save("fact", "existing", "Old version")
        with self.assertRaisesRegex(ValueError, "differs"):
            migrate_facts()
        self.assertEqual(read_fact("existing")["fact"].strip(), "New version")
        with database() as db:
            self.assertEqual(db.execute("SELECT body FROM entries").fetchone()[0], "Old version")
        (self.root / "Inbox/existing.md").rename(self.root / "Inbox/renamed.md")
        migrate_facts()
        self.assertEqual(len(recall_facts("version")), 2)

    def test_external_edits_properties_and_moves(self):
        remember_fact("Editor", "Initial", "Preferences")
        note = self.root / "Preferences/Editor.md"
        header = b"\xef\xbb\xbf---\r\ntags: [custom]\r\n---\r\n"
        note.write_bytes(header + b"Line one\r\nLine two\r\n")
        edit_fact("editor", "Line two", "Updated")
        self.assertEqual(note.read_bytes(), header + b"Line one\r\nUpdated\r\n")
        with self.assertRaises(ValueError):
            edit_fact("editor", "Line two", "Stale")
        note.rename(self.root / "Projects/Editor.md")
        self.assertEqual(recall_facts("UPDATED")[0]["category"], "Projects")
        remember_fact("editor", "Replacement")
        self.assertTrue((self.root / "Projects/Editor.md").read_bytes().startswith(header))

    def test_duplicate_names_and_ambiguous_edits(self):
        remember_fact("Note", "aaa", "People")
        remember_fact("Note", "Other", "Projects")
        with self.assertRaisesRegex(ValueError, "Several"):
            forget_fact("Note")
        with self.assertRaisesRegex(ValueError, "exactly once"):
            edit_fact("Note", "aa", "x", "People")
        with self.assertRaises(ValueError):
            remember_fact("Another", "Data", "../outside")
        forget_fact("Note", "People")
        self.assertEqual(read_fact("Note")["fact"].strip(), "Other")
