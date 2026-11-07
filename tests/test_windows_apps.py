from unittest import TestCase
from unittest.mock import patch

from tools._windows_apps import App, matches
from tools.open_app.tool import launch


class WindowsAppsTests(TestCase):
    def test_names_are_whole_words_and_exact_matches_win(self):
        apps = [App("OBS Studio", "obs"), App("Obsidian", "notes"), App("OBS Studio Help", "help")]
        self.assertEqual(matches("OBS", apps), [apps[0]])
        self.assertEqual(matches("OBS Studio", apps), [apps[0]])
        self.assertFalse(matches("OBS && calc.exe", apps))

    def test_installed_product_is_not_confused_with_a_different_launcher(self):
        product = App("Composer", location="C:/Composer")
        other = App("Composer Viewer", "viewer", "C:/Viewer/viewer.exe")
        self.assertEqual(matches("Composer", [product, other]), [product])

    def test_only_a_unique_registered_entry_is_launched(self):
        apps = [App("Music Studio", "music"), App("Video Studio", "video"), App("Widget", location="C:/Apps")]
        with patch("tools.open_app.tool.catalog", return_value=apps), patch("os.startfile", create=True) as start:
            self.assertEqual(launch("Studio")["status"], "ambiguous")
            self.assertEqual(launch("Widget")["status"], "not_launchable")
            self.assertEqual(launch("Missing")["status"], "not_found")
            start.assert_not_called()
            self.assertEqual(launch("Video Studio")["status"], "launch_requested")
            start.assert_called_once_with(r"shell:AppsFolder\video")
