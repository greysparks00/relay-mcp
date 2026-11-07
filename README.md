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

## Inspect or download the vault on another PC

The server can produce a current ZIP of Relay's Markdown notes. It includes Home.md and notes directly inside the seven Relay category folders, including Handoffs. Other folders, attachments, hidden files, links and Obsidian configuration are outside the export. An export takes the vault lock while reading. Direct writes by other editors do not take that lock. The archive is a current snapshot; each successful pull replaces the previous local ZIP.

### Enroll a PC

1. On the PC, create a dedicated key with `ssh-keygen -t ed25519 -f ~/.ssh/relay_vault`. Load a passphrase-protected key into the SSH agent used by your download task. Give each PC its own key.
2. On DietPi/Linux, append **one line per PC** to the Relay service account's `~/.ssh/authorized_keys`. Replace the three absolute paths below with your actual vault, interpreter and script, and replace the public-key placeholder with the PC's complete public key. Keep the command fixed and the `restrict` prefix. Protect the account's SSH directory and authorized_keys with modes 700 and 600.

   ```text
   restrict,command="env RELAY_MCP_VAULT_DIR='/home/relay/relay-vault' '/opt/relay-mcp/.venv/bin/python' '/opt/relay-mcp/vault_export.py'" ssh-ed25519 AAAA... pc-name
   ```

3. On the PC, add this alias to `~/.ssh/config`. Set HostName to the address you already use for SSH and User to the account from step 2.

   ```text
   Host relay-vault
       HostName dietpi
       User relay
       IdentityFile ~/.ssh/relay_vault
       IdentitiesOnly yes
   ```

4. Verify the host's key fingerprint against the one shown on the server (for example, `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`). During enrollment, `ssh -T relay-vault verify-enrollment` should ask you to trust the verified host key on first contact, then return “This key only permits relay-vault-export.” The pull helper requires an already trusted host key.

### Browse and refresh

Copy `vault_pull.py` to the PC. It needs Python 3.11+ and the OpenSSH client. Run the following from a private directory writable only by your user. Open the ZIP in your file browser to inspect individual Markdown notes, or extract a copy for Obsidian.

```sh
python vault_pull.py relay-vault relay-memory.zip
```

For continuous refresh, run `python vault_pull.py relay-vault relay-memory.zip --watch 60`. It checks immediately and once per minute while running. If SSH is offline or the archive is incomplete, the previous good copy stays available. Use absolute paths for the interpreter, script and ZIP when scheduling it. On Windows, create a Task Scheduler task **At log on** for your user with the watch command. On Linux, run it as a systemd user service or schedule the one-shot command from cron with access to the SSH key or agent.

Remove a PC's public-key line on the server to revoke future connections. Archives already downloaded remain on that PC. Store the ZIP in a private folder on an encrypted drive if the notes are sensitive.
