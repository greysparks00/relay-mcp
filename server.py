import os
from pathlib import Path

from dotenv import load_dotenv
import uvicorn
from mcp.server import MCPServer

from health import register_health
from tools import load_tools
from tools._vault import vault

load_dotenv(Path(__file__).with_name(".env"))

def configure_display():
    profile = os.getenv("RELAY_ENV")
    if profile is None:
        return
    
    if profile not in ("development", "production"):
        raise ValueError("RELAY_ENV must be development or production")
    
    prefix = f"RELAY_{profile.upper()}_DISPLAY"

    for field in ("URL", "TOKEN"):
        value = os.getenv(f"{prefix}_{field}")

        if not value:
            raise ValueError(f"Set {prefix}_{field} for the selected environment")
        
        os.environ[f"RELAY_DISPLAY_{field}"] = value


configure_display()

# Initialize the vault before accepting health probes or tool requests.
with vault():
    pass

mcp = MCPServer("Relay")
failed_tools = load_tools(mcp)
register_health(mcp, failed_tools)

def run_server(port: int = 18000) -> None:
    host = "0.0.0.0"
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
