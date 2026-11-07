from unittest import TestCase
from unittest.mock import patch

from tools._timers import Timers
from tools.convert_timezone.tool import convert_timezone
from tools.convert_units.tool import convert_units
from tools.date_math.tool import date_math


class VoiceToolTests(TestCase):
    def test_timer_expiry_and_reuse(self):
        timers = Timers()
        with patch("tools._timers.monotonic", return_value=100):
            timers.start("Pasta", 10)
            with self.assertRaises(ValueError):
                timers.start("pasta", 20)
        with patch("tools._timers.monotonic", return_value=110):
            self.assertEqual(timers.check("PASTA")[0]["state"], "expired")
            timers.start("Pasta", 20)
            self.assertEqual(timers.cancel(" pasta ")["state"], "cancelled")
            self.assertEqual(timers.check(None), [])

    def test_daylight_saving_gap_and_repeated_hour(self):
        zones = ("America/Chicago", "Europe/London")
        with self.assertRaisesRegex(ValueError, "does not exist"):
            convert_timezone("2026-03-08T02:30", *zones)
        repeated = "2026-11-01T01:30"
        with self.assertRaisesRegex(ValueError, "twice"):
            convert_timezone(repeated, *zones)
        self.assertIn("06:30", convert_timezone(repeated, *zones, "earlier")["target_time"])
        self.assertIn("07:30", convert_timezone(repeated, *zones, "later")["target_time"])

    def test_temperature_volume_and_incompatible_units(self):
        self.assertEqual(convert_units(180, "degrees Celsius", "Fahrenheit")["value"], 356)
        self.assertEqual(convert_units(1, "US cups", "fluid ounces")["value"], 8)
        with self.assertRaises(ValueError):
            convert_units(1, "ounce", "fluid ounce")

    def test_date_offsets_and_signed_intervals(self):
        self.assertEqual(date_math("2024-02-28", days=1)["date"], "2024-02-29")
        self.assertEqual(date_math("2026-11-07", end="2026-11-01")["days"], -6)
