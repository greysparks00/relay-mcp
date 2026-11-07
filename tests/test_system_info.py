from unittest import TestCase
from unittest.mock import patch

from tools.get_system_info import sensors
from tools.get_system_info.tool import snapshot


class SystemInfoTests(TestCase):
    def test_unavailable_gpu_readings_and_real_zero(self):
        self.assertIsNone(sensors.number("[N/A]"))
        self.assertIsNone(sensors.number("nan"))
        self.assertEqual(sensors.number("0"), 0)

    def test_memory_query_skips_hardware_sensor_probes(self):
        with patch("tools.get_system_info.tool.hardware_snapshot", side_effect=AssertionError):
            memory = snapshot("memory")["memory"]
        self.assertEqual(memory["used_bytes"] + memory["available_bytes"], memory["total_bytes"])

    def test_only_device_temperatures_are_attributed(self):
        def reading(kind, label, value):
            return {"kind": kind, "device": "test device", "label": label, "value": value}

        data = {"adapters": ["test device"], "readings": [
            reading("Mainboard", "CPU", 60), reading("Cpu", "Distance to TjMax", 70),
            reading("Cpu", "Package", 50), reading("GpuAmd", "GPU Core", 40)]}
        with patch.object(sensors, "windows_sensors", return_value=data), patch.object(sensors, "nvidia_gpus", return_value=[]), patch.object(sensors.os, "name", "nt"):
            cpu, graphics = sensors.hardware_snapshot(True)
        self.assertEqual([item["celsius"] for item in cpu], [50])
        self.assertEqual(graphics[0]["temperature_c"], 40)
