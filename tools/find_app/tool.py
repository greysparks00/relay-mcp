import asyncio

from tools._windows_apps import search


async def find_app(name: str) -> dict:
    """Find a Windows application by display name on the Relay server PC. Returns registered launch IDs and known file or install locations; install-only records have no launch ID."""
    return await asyncio.to_thread(search, name)
