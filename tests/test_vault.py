import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from tools.delete_handoff.tool import delete_handoff
from tools.list_handoffs.tool import list_handoffs
from tools.resume_handoff.tool import resume_handoff
from tools.save_handoff.tool import save_handoff
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

    def test_handoffs_are_editable_notes_separate_from_facts(self):
        topic = "../CON"
        remember_fact(topic, "Fact")
        save_handoff(topic, "Checkpoint")
        note, = (self.root / "Handoffs").glob("*.md")
        note.write_text(note.read_text().replace("Checkpoint", "Edited by hand"))
        handoff = resume_handoff(topic)
        self.assertEqual(handoff["summary"], "Edited by hand")
        self.assertEqual(list_handoffs(), [{"topic": topic.casefold(), "updated_at": handoff["updated_at"]}])
        save_handoff(topic, "Revised")
        self.assertEqual(resume_handoff(topic)["summary"], "Revised")
        self.assertEqual(len(recall_facts("")), 1)
        delete_handoff(topic)
        self.assertFalse(note.exists())
        self.assertEqual(read_fact(topic)["fact"].strip(), "Fact")
        with self.assertRaisesRegex(ValueError, "No handoff"):
            resume_handoff(topic)

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
