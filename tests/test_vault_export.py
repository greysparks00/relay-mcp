import io
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from zipfile import BadZipFile, ZipFile

from tools.remember_fact.tool import remember_fact
from vault_export import export
from vault_pull import pull


class VaultExportTests(TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(TemporaryDirectory()))
        self.root = self.base / "vault"
        self.enterContext(patch.dict(os.environ, {"RELAY_MCP_VAULT_DIR": str(self.root)}))
        remember_fact("café", "First version")

    def snapshot(self):
        destination = io.BytesIO()
        export(destination)
        return destination.getvalue()

    def test_contents_privacy_and_freshness(self):
        (self.root / ".obsidian").mkdir()
        (self.root / ".obsidian/secret.md").write_text("private")
        (self.root / "Inbox/.private.md").write_text("private")
        outside = self.base / "private"
        outside.write_text("private")
        os.link(outside, self.root / "Inbox/hardlink.md")
        first = self.snapshot()
        self.assertEqual(first, self.snapshot())
        with ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual([n for n in archive.namelist() if not n.endswith("/")], ["Inbox/café.md"])
        remember_fact("café", "Edited")
        with ZipFile(io.BytesIO(self.snapshot())) as archive:
            self.assertIn(b"Edited", archive.read("Inbox/café.md"))
        (self.root / "Inbox/café.md").unlink()
        with ZipFile(io.BytesIO(self.snapshot())) as archive:
            self.assertNotIn("Inbox/café.md", archive.namelist())

    def test_download_replacement_and_failure_recovery(self):
        output = self.base / "private" / "vault.zip"
        data = self.snapshot()

        def deliver(command, **options):
            self.assertIn("StrictHostKeyChecking=yes", command)
            options["stdout"].write(data)

        with patch("vault_pull.subprocess.run", side_effect=deliver):
            self.assertTrue(pull("my-dietpi", output))
            self.assertFalse(pull("my-dietpi", output))
            good = output.read_bytes()
            data = b"incomplete transfer"
            with self.assertRaises(BadZipFile):
                pull("my-dietpi", output)
        with patch("vault_pull.subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 120)):
            with self.assertRaises(subprocess.TimeoutExpired):
                pull("my-dietpi", output)
        self.assertEqual(output.read_bytes(), good)
        self.assertEqual(list(output.parent.iterdir()), [output])
