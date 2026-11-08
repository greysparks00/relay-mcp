# Sending content to a screen

Relay calls `change_screen(id=1, screen={"type":"text","content":"Hello"})`. The MCP tool sends one request to the separate screen server:

```http
POST /v1/screens/send
Content-Type: application/json

{"id":1,"screen":{"type":"text","content":"Hello"}}
```

In `relay-mcp/.env`, set `RELAY_DISPLAY_URL` to the server origin; it defaults to `http://127.0.0.1:8766` on the Pi. Remote origins use HTTPS. Set `RELAY_DISPLAY_TOKEN` to supply the sender's bearer credential.

## Registration and routing protocol

The sibling project `relay-displays` implements this protocol. Its README covers starting the server and connecting the raw JSON page for screen 1.

1. A display opens a persistent WebSocket to `/v1/screens/{id}/connect` on the screen server. Enter the shared key from `relay-displays/.env` to claim the ID in the URL. Screen 1 can connect from the same Pi. Other devices can connect outbound over WSS.
2. Register the authenticated connection in a live map keyed by ID. Reject an additional connection claiming an active ID. Remove disconnected sessions and permit fresh registration.
3. On a POST, forward the JSON object only to the live socket registered for the requested ID. After forwarding, return HTTP 200 or 202 with `{"id":1,"status":"accepted"}`. This acknowledges forwarding; rendering requires a separate acknowledgement from the display.
4. If the screen ID has no active connection, discard the request and return HTTP 409. A failed connection leaves delivery unconfirmed; Relay does not retry or queue the POST.

The initial screen page displays the raw JSON with textContent. Template rendering belongs to a future version of that page.

The screen object is either `{"type":"text","content":"..."}` or `{"type":"comparison","option1":"...","option2":"..."}`. The agent writes the display copy. Each text field accepts up to 8192 characters. Comparison options must be nonempty.
