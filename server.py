import uvicorn
from mcp.server import MCPServer

from health import register_health
from tools import load_tools
from tools._vault import vault

# Initialize the vault before accepting health probes or tool requests.
with vault():
    pass
mcp = MCPServer("Relay")
failed_tools = load_tools(mcp)
register_health(mcp, failed_tools)


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
