"""Resolve Windows display names using the current user's AppsFolder and install records."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import subprocess
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class App:
    name: str
    app_id: str = ""
    location: str = ""


# AppsFolder preserves the registered launch identity, including shortcut arguments.
# The command is constant: user input never enters PowerShell or a shell command.
CATALOG_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$items = (New-Object -ComObject Shell.Application).Namespace('shell:AppsFolder').Items()
$apps = foreach ($item in $items) {
    [pscustomobject]@{name=$item.Name; app_id=$item.Path; location=[string]$item.ExtendedProperty('System.Link.TargetParsingPath')}
}
ConvertTo-Json -InputObject @($apps) -Compress
"""


def installed_records():
    import winreg

    path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_READ | view) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            key = winreg.EnumKey(root, index)
                            with winreg.OpenKey(root, key) as entry:
                                name = winreg.QueryValueEx(entry, "DisplayName")[0]
                                try:
                                    location = winreg.QueryValueEx(entry, "InstallLocation")[0]
                                except FileNotFoundError:
                                    location = ""
                                if isinstance(name, str) and name.strip():
                                    yield App(name=name.strip(), location=location or "")
                        except OSError:
                            continue
            except OSError:
                continue


_lock = Lock()
_catalog = ()
_expires = 0.0


def catalog():
    global _catalog, _expires
    if os.name != "nt":
        raise ValueError("App discovery currently supports Windows.")
    with _lock:
        if monotonic() < _expires:
            return _catalog
        powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        result = subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-Command", CATALOG_SCRIPT],
                                capture_output=True, encoding="utf-8", check=True, timeout=12,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        apps = [App(**item) for item in json.loads(result.stdout) if item["name"] and item["app_id"]]
        _catalog = tuple(dict.fromkeys([*apps, *installed_records()]))
        _expires = monotonic() + 45
        return _catalog


def words(name):
    return " ".join(re.findall(r"[\w+#]+", name.casefold()))


def matches(query, apps):
    query = query.strip()
    key = words(query)
    if not key or len(query) > 256:
        raise ValueError("Provide an app name between 1 and 256 characters.")
    launchers, records = [], []
    for app in apps:
        name = words(app.name)
        if app.app_id and app.app_id.casefold() == query.casefold():
            return [app]
        if f" {key} " not in f" {name} ":
            continue
        # "Open Widget" should never select "Uninstall Widget" or its help file.
        if name != key and re.search(r"\b(uninstall|uninstaller|repair|setup|help|manual|updates?)\b", name):
            continue
        (launchers if app.app_id else records).append(app)
    # A registry-only exact name can be a different product from a partially
    # matching launcher. Only associate it with an app in its install directory.
    exact_records = [app for app in records if app.name.casefold() == query.casefold()]
    if exact_records and not any(app.name.casefold() == query.casefold() for app in launchers):
        linked = [app for app in launchers if app.location and any(
            record.location and Path(app.location).is_relative_to(Path(record.location))
            for record in exact_records)]
        if linked:
            launchers = linked
        elif launchers:
            # A version suffix (Blender 4.4) is common when the uninstall entry
            # omits the version. Otherwise let the caller choose the full name.
            versioned = [app for app in launchers if re.fullmatch(re.escape(key) + r" (?:v?\d+)(?: \d+)*", words(app.name))]
            if not versioned:
                return exact_records
            launchers = versioned
    candidates = launchers or records
    exact = [app for app in candidates if app.name.casefold() == query.casefold()]
    return sorted(exact or candidates, key=lambda app: (len(words(app.name)), app.name.casefold(), app.app_id))


def describe(apps):
    return [asdict(app) for app in apps[:10]]


def search(name):
    found = matches(name, catalog())
    return {"status": "found" if found else "not_found", "count": len(found), "matches": describe(found)}
