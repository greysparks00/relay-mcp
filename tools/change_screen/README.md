# Display coordinator contract

`change_screen(screen_id, template, text="")` is a regular MCP tool. The model supplies a positive screen number, a lowercase template ID (for example, `dashboard`), and up to 8192 characters of plain text. An omitted text value sends an empty string.

Set `RELAY_DISPLAY_URL` in the MCP server environment to the coordinator's origin. The default is `http://127.0.0.1:8766` for a separate process on the same Pi. Remote origins require HTTPS. If `RELAY_DISPLAY_TOKEN` is set, the tool sends it as a bearer token.

Example request:

```http
PUT /v1/screens/1/state
Content-Type: application/json

{"template":"dashboard","text":"Welcome home"}
```

Respond with HTTP 200 or 202 and a small JSON acknowledgement, for example `{"screen_id":1,"status":"queued"}`. Use `queued` when holding the state for a disconnected screen and `accepted` when taking responsibility for delivery. Return 404 for an unknown screen ID. A timeout leaves delivery unconfirmed. Repeating a PUT requests the same desired screen state.

## Suggested kiosk design

Run the coordinator as its own service alongside MCP. Give each kiosk an ID and a credential scoped to that ID. Screen 1 can run Chromium in kiosk mode on the Pi and load a screen-specific page from the display service. A future screen on a different computer can load its own page and connect outbound over WSS.

The coordinator can store one latest state per screen, assign it a revision, and send it to the matching connection when the state changes or the kiosk reconnects. The kiosk maps template IDs to built-in layouts and inserts the supplied text using `textContent`. A later data source can populate other fields in the same layout. If physical display status matters, have the kiosk acknowledge the revision after rendering.
