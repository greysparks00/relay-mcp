"""Read optional hardware sensors without elevation or driver installation."""

import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from threading import Lock
from time import monotonic

import psutil


def output(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=4, check=True,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def nvidia_gpus() -> list[dict]:
    if os.name == "nt":
        executable = Path(os.environ["SystemRoot"]) / "System32/nvidia-smi.exe"
        if not executable.is_file():
            return []
    else:
        executable = shutil.which("nvidia-smi")
        if not executable:
            return []
    query = "name,temperature.gpu,utilization.gpu,memory.used,memory.total"
    data = output([str(executable), "--query-gpu=" + query, "--format=csv,noheader,nounits"])
    cards = []
    for row in csv.reader(data.splitlines(), skipinitialspace=True):
        if len(row) == 5:
            cards.append(dict(name=row[0], temperature_c=number(row[1]), usage_percent=number(row[2]),
                              vram_used_mib=number(row[3]), vram_total_mib=number(row[4])))
    return cards


# Query the monitor's hardware tree so a motherboard sensor never becomes a CPU reading.
WINDOWS_QUERY = r"""
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$adapters = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object Name)
$readings = foreach ($ns in 'root/LibreHardwareMonitor','root/OpenHardwareMonitor') {
    $hardware = @(Get-CimInstance -Namespace $ns -ClassName Hardware -ErrorAction SilentlyContinue)
    if (-not $hardware) { continue }
    $devices = @{}
    foreach ($h in $hardware) { $devices[$h.Identifier] = $h }
    foreach ($s in (Get-CimInstance -Namespace $ns -ClassName Sensor -Filter "SensorType='Temperature'" -ErrorAction SilentlyContinue)) {
        $parent = $devices[$s.Parent]
        if ($parent -and $null -ne $s.Value) {
            [pscustomobject]@{kind=$parent.HardwareType; device=$parent.Name; label=$s.Name; value=$s.Value}
        }
    }
}
@{adapters=$adapters; readings=@($readings | Where-Object {$_})} | ConvertTo-Json -Depth 4 -Compress
"""


# When no monitor is publishing readings, recheck its availability and the display
# inventory every 30 seconds. Driver telemetry and any available sensors stay live.
_windows_lock = Lock()
_inventory_expires = 0.0
_adapters: list[str] = []


def windows_sensors() -> dict:
    global _adapters, _inventory_expires
    with _windows_lock:
        if monotonic() < _inventory_expires:
            return {"adapters": _adapters, "readings": []}
        shell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        raw = output([str(shell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_QUERY])
        try:
            data = json.loads(raw)
        except ValueError:
            return {"adapters": [], "readings": []}
        if not data["readings"]:
            _adapters = data["adapters"]
            _inventory_expires = monotonic() + 30
        return data


def linux_cpu_zones(root: Path = Path("/sys/class/thermal")) -> list[dict]:
    """Some ARM boards expose CPU temperatures through thermal zones only."""
    readings = []
    for zone in sorted(root.glob("thermal_zone*")):
        try:
            label = (zone / "type").read_text().strip()
            if label.lower().replace("-", "_") not in {"cpu_thermal", "cpu_thermal_zone", "cpu_therm"}:
                continue
            value = number((zone / "temp").read_text().strip())
            if value is not None:
                readings.append({"sensor": label, "celsius": value / 1000})
        except OSError:
            continue
    return readings


def hardware_snapshot(include_gpu: bool) -> tuple[list[dict], list[dict]]:
    cards = nvidia_gpus() if include_gpu else []
    cpu = []
    if os.name == "nt":
        data = windows_sensors()
        # Preserve distinct adapters even when two boards report the same model.
        names = [card["name"].casefold() for card in cards]
        if include_gpu:
            for name in data["adapters"]:
                if name.casefold() in names:
                    names.remove(name.casefold())
                else:
                    cards.append({"name": name, "temperature_c": None})
        for sensor in data["readings"]:
            value = number(sensor["value"])
            if value is None:
                continue
            kind = sensor["kind"].casefold()
            if kind == "cpu" and "distance" not in sensor["label"].casefold():
                cpu.append({"sensor": sensor["device"] + " " + sensor["label"], "celsius": value})
            elif include_gpu and kind.startswith("gpu") and sensor["label"].lower() in {"gpu core", "gpu temperature"}:
                matches = [card for card in cards if card["name"].casefold() == sensor["device"].casefold()]
                if len(matches) == 1 and matches[0]["temperature_c"] is None:
                    matches[0]["temperature_c"] = value
    elif hasattr(psutil, "sensors_temperatures"):
        try:
            sensors = psutil.sensors_temperatures()
        except OSError:
            sensors = {}
        for chip, readings in sensors.items():
            if chip in {"coretemp", "k10temp", "zenpower", "cpu_thermal"}:
                for sensor in readings:
                    value = number(sensor.current)
                    if value is not None:
                        cpu.append({"sensor": sensor.label or chip, "celsius": value})
    if os.name == "posix" and not cpu:
        cpu = linux_cpu_zones()
    return cpu, cards
