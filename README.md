# Relay MCP server

Run the server from this repository on Windows or Linux with Python 3.13 or newer and `uv`.

```sh
uv run --locked --python 3.13 server.py
```

The server listens on `127.0.0.1:8000`. The MCP endpoint is `/mcp` and the dashboard health endpoint is `/health`. Press Ctrl+C for a graceful shutdown.

## Running on DietPi or another Linux host

Use a writable vault directory on the server. For example, in the shell that starts Relay:

```sh
export RELAY_MCP_VAULT_DIR="$HOME/relay-vault"
uv run --locked --python 3.13 server.py
```

The default is the repository's `vault` directory. The service account needs permission to create and replace files in the vault. Use a local filesystem such as ext4 that supports file locking, hard links and atomic renames. Facts and conversation handoffs persist as Markdown. Timers last for the lifetime of the server process. Hardware readings come from the server and depend on available sensors.

To use a Windows or Linux chat client on another computer, run this SSH tunnel **on the client**, replacing the SSH destination with the server's account and hostname:

```sh
ssh -N -L 127.0.0.1:8765:127.0.0.1:8000 user@dietpi
```

Leave the tunnel running. In the client project's `.env`, set `RELAY_MCP_URL=http://127.0.0.1:8765/mcp` and start Relay chat. Visit `http://127.0.0.1:8765/health` to check connectivity. When both programs are on one computer, the client defaults to `http://127.0.0.1:8000/mcp`.

App discovery and launching belong to the chat client. An “open app” request runs on the computer where that client is running. The MCP server does not register either app tool.
