import asyncio
import os
import re

from tools._windows_apps import catalog, describe, matches, words


def launch(name: str) -> dict:
    found = matches(name, catalog())
    if not found:
        return {"status": "not_found"}
    if len(found) > 1:
        return {"status": "ambiguous", "count": len(found), "matches": describe(found)}
    app = found[0]
    if not app.app_id or re.search(r"\b(uninstall|uninstaller|repair|setup)\b", words(app.name)):
        return {"status": "not_launchable", "name": app.name, "location": app.location}

    # Use only the catalog identity. Windows resolves the entry and its registered
    # arguments for both desktop and Store apps, without interpreting command text.
    os.startfile("shell:AppsFolder\\" + app.app_id)
    return {"status": "launch_requested", "name": app.name}


async def open_app(name: str) -> dict:
    """Open one installed Windows app by display name or a launch ID from find_app. Returns alternatives for ambiguous names. Accepts no command-line arguments."""
    return await asyncio.to_thread(launch, name)
