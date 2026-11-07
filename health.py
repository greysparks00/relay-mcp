"""Dashboard readiness checks. A stopped process cannot answer an HTTP probe."""

import asyncio
from contextlib import closing
import os
from pathlib import Path
import sqlite3

from starlette.responses import JSONResponse

from tools._vault import CATEGORIES, PROJECT, require_local, vault_root


def storage_issues() -> list[str]:
    issues = []
    try:
        root = vault_root()
        for category in CATEGORIES:
            folder = root / category
            require_local(folder)
            with os.scandir(folder) as items:
                next(items, None)
    except (OSError, ValueError):
        issues.append("vault_unavailable")

    directory = Path(os.environ.get("RELAY_MCP_DATA_DIR") or PROJECT / "data")
    database = directory / "relay.sqlite3"
    try:
        if database.exists():
            with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.2)) as db:
                db.execute("SELECT kind, name, body, updated_at FROM entries LIMIT 0")
        elif directory.exists() and not directory.is_dir():
            issues.append("handoff_storage_unavailable")
    except (OSError, sqlite3.Error):
        issues.append("handoff_storage_unavailable")
    return issues


def register_health(server, failed_tools: list[str]) -> None:
    @server.custom_route("/health", methods=["GET"])
    async def health(request):
        issues = await asyncio.to_thread(storage_issues)
        try:
            registered = sorted(await server.list_tools(), key=lambda tool: tool.name)
            tools = [{"name": tool.name, "description": tool.description} for tool in registered]
            if not tools:
                issues.append("no_tools_registered")
        except Exception:
            tools = None
            issues.append("registry_unavailable")
        if failed_tools:
            issues.append("tool_registration_failed")
        return JSONResponse({
            "status": "degraded" if issues else "healthy",
            "tool_count": len(tools) if tools is not None else None,
            "tools": tools,
            "failed_tools": failed_tools,
            "issues": issues,
        }, status_code=503 if issues else 200, headers={"Cache-Control": "no-store"})
