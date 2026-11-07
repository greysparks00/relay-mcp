import uvicorn
from mcp.server import MCPServer

from tools import load_tools
from tools._migrate_facts import migrate_facts

migrate_facts()
mcp = MCPServer("Relay")
load_tools(mcp)


def run_server(port: int = 8000) -> None:
    host = "127.0.0.1"
    uvicorn.run(
        mcp.streamable_http_app(host=host),
        host=host,
        port=port,
        lifespan="on",
        timeout_graceful_shutdown=15,
        log_level=mcp.settings.log_level.lower(),
    )


if __name__ == "__main__":
    run_server()
