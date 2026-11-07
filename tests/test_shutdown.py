import asyncio
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase

from mcp import Client


# Signal the server during a real HTTP tool call, then finish a vault write.
SERVER = """
import asyncio, os, signal
from server import mcp, run_server
from tools.remember_fact.tool import remember_fact

@mcp.tool()
async def remember_during_shutdown() -> str:
    if os.name == "nt":
        os.kill(0, signal.CTRL_C_EVENT)
    else:
        os.kill(os.getpid(), signal.SIGINT)
    await asyncio.sleep(0.8)
    return remember_fact("Shutdown check", "Saved before exit")

run_server(port=0)
"""


class ShutdownTests(IsolatedAsyncioTestCase):
    async def test_interrupt_drains_tool_and_releases_listener(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "vault"
            log = root / "server.log"
            options = {}
            if os.name == "nt":
                # Isolate the console event from the test runner and user's shell.
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = subprocess.SW_HIDE
                options.update(creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=startup)

            with log.open("wb") as output:
                process = subprocess.Popen(
                    [sys.executable, "-c", SERVER],
                    cwd=Path(__file__).resolve().parents[1],
                    env={**os.environ, "RELAY_MCP_DATA_DIR": directory, "RELAY_MCP_VAULT_DIR": str(vault)},
                    stdout=output, stderr=subprocess.STDOUT, **options,
                )
                try:
                    async with asyncio.timeout(25):
                        while True:
                            logs = log.read_text(errors="replace")
                            match = re.search(r"Uvicorn running on http://127\.0\.0\.1:(\d+)", logs)
                            if match:
                                break
                            self.assertIsNone(process.poll(), logs)
                            await asyncio.sleep(0.05)
                        port = int(match[1])
                        async with Client(f"http://127.0.0.1:{port}/mcp") as client:
                            await client.list_tools()
                            result = await client.call_tool("remember_during_shutdown", {})
                            self.assertFalse(result.is_error)
                            self.assertIn("Remembered", result.content[0].text)
                        await asyncio.to_thread(process.wait, 10)
                except Exception as error:
                    error.add_note(log.read_text(errors="replace"))
                    raise
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait(5)
            logs = log.read_text(errors="replace")
            self.assertEqual(process.returncode, 0, logs)
            self.assertIn("Application shutdown complete", logs)
            self.assertNotIn("Traceback", logs)
            self.assertIn("Saved before exit", (vault / "Inbox/Shutdown check.md").read_text())
            with socket.socket() as probe:
                probe.settimeout(0.25)
                self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)
