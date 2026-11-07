import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch

from tools._vault import vault_root
from tools.get_system_info.sensors import linux_cpu_zones
from tools.read_fact.tool import read_fact
from tools.remember_fact.tool import remember_fact


class LinuxStorageTests(TestCase):
    @skipUnless(os.name == "posix", "POSIX filesystem behavior")
    def test_vault_expansion_and_symlink_isolation(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"HOME": temp, "RELAY_MCP_VAULT_DIR": "~/my vault"}):
            root = Path(temp) / "my vault"
            self.assertEqual(vault_root(), root)
            remember_fact("café", "A local note")
            self.assertEqual(read_fact("CAFÉ")["fact"].strip(), "A local note")
            outside = Path(temp) / "outside.md"
            outside.write_text("private")
            (root / "Inbox/linked.md").symlink_to(outside)
            with self.assertRaises(ValueError):
                read_fact("linked")
            with self.assertRaises(ValueError):
                remember_fact("linked", "overwrite")
            self.assertEqual(outside.read_text(), "private")

    def test_arm_cpu_zone_excludes_unrelated_devices(self):
        with TemporaryDirectory() as temp:
            for i, name in enumerate(["cpu-thermal", "battery"]):
                zone = Path(temp) / f"thermal_zone{i}"
                zone.mkdir()
                (zone / "type").write_text(name)
                (zone / "temp").write_text("43250")
            self.assertEqual(linux_cpu_zones(Path(temp)), [{"sensor": "cpu-thermal", "celsius": 43.25}])
