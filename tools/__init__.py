"""Each public subfolder supplies tool.py with a function named after the folder."""

from importlib import import_module
from pathlib import Path

from mcp.server import MCPServer


def load_tools(server: MCPServer) -> None:
    for folder in sorted(Path(__file__).parent.iterdir()):
        if not folder.is_dir() or folder.name.startswith(("_", ".")):
            continue
        if not folder.name.isidentifier() or not (folder / "tool.py").is_file():
            raise ValueError(f"Expected a Python tool folder with tool.py: {folder}")

        module = import_module(f".{folder.name}.tool", __package__)
        handler = getattr(module, folder.name, None)
        if not callable(handler):
            raise ValueError(f"{folder}/tool.py must define {folder.name}()")
        server.tool(name=folder.name)(handler)
