import asyncio
from datetime import UTC, datetime
import os
from pathlib import Path
import platform
import time
from typing import Literal

import psutil

from .sensors import hardware_snapshot


Section = Literal["overview", "cpu", "gpu", "memory", "disk", "temperatures", "cpu_temperature", "gpu_temperature"]


def processor_name() -> str:
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return platform.processor() or platform.machine()


def snapshot(section: Section) -> dict:
    result = {}
    if section == "overview":
        result["system"] = {"os": platform.platform(), "architecture": platform.machine(),
                            "uptime_seconds": max(0, int(time.time() - psutil.boot_time()))}
    if section in {"cpu", "overview"}:
        result["cpu"] = {"model": processor_name(), "physical_cores": psutil.cpu_count(logical=False),
                         "logical_processors": psutil.cpu_count(), "usage_percent": psutil.cpu_percent(interval=0.1)}
    if section in {"memory", "overview"}:
        memory = psutil.virtual_memory()
        result["memory"] = {"total_bytes": memory.total, "available_bytes": memory.available,
                            "used_bytes": memory.total - memory.available, "usage_percent": memory.percent}
    if section in {"disk", "overview"}:
        drive = Path(os.environ.get("SystemRoot", "/")).anchor or "/"
        disk = psutil.disk_usage(drive)
        result["system_disk"] = {"drive": drive, "total_bytes": disk.total,
                                 "free_bytes": disk.free, "usage_percent": disk.percent}
    if section in {"overview", "gpu", "temperatures", "cpu_temperature", "gpu_temperature"}:
        cpu, cards = hardware_snapshot(include_gpu=section != "cpu_temperature")
        if section in {"overview", "temperatures", "cpu_temperature"}:
            result["cpu_temperature_sensors"] = cpu
        if section != "cpu_temperature":
            result["gpus"] = cards
    result["sampled_at"] = datetime.now(UTC).isoformat()
    return result


async def get_system_info(section: Section = "overview") -> dict:
    """Get live details of the Relay server computer: OS, CPU load and cores, RAM, system disk, GPUs, VRAM and available Celsius temperatures. Choose a section for a targeted answer. Empty sensor lists or null readings mean unavailable."""
    return await asyncio.to_thread(snapshot, section)
