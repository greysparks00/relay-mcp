"""Each public subfolder supplies tool.py with a function named after the folder."""

from importlib import import_module
import logging
from pathlib import Path

from mcp.server import MCPServer


def load_tools(server: MCPServer) -> list[str]:
    failed = []
    for folder in sorted(Path(__file__).parent.iterdir()):
        if not folder.is_dir() or folder.name.startswith(("_", ".")):
            continue
        try:
            if not folder.name.isidentifier() or not (folder / "tool.py").is_file():
                raise ValueError("Expected a Python tool folder with tool.py")
            module = import_module(f".{folder.name}.tool", __package__)
            handler = getattr(module, folder.name)
            if not callable(handler):
                raise ValueError(f"Expected callable {folder.name}()")
            server.tool(name=folder.name)(handler)
        except Exception:
            logging.exception("Failed to load tool %s", folder.name)
            failed.append(folder.name)
    return failed
