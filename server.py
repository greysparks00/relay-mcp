from datetime import datetime
from mcp.server import MCPServer

mcp = MCPServer("Relay")

@mcp.tool()
def get_current_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().astimezone().isoformat()

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000
    )