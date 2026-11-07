"""Dashboard readiness checks. A stopped process cannot answer an HTTP probe."""

import asyncio
import os

from starlette.responses import JSONResponse

from tools._vault import VAULT_FOLDERS, require_local, vault_root


def storage_issues() -> list[str]:
    issues = []
    try:
        root = vault_root()
        for category in VAULT_FOLDERS:
            folder = root / category
            require_local(folder)
            with os.scandir(folder) as items:
                next(items, None)
    except (OSError, ValueError):
        issues.append("vault_unavailable")

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
