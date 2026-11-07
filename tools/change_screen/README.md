# Display coordinator contract

`change_screen(screen_id, template, text="")` is a regular MCP tool. The model supplies a positive screen number, a lowercase template ID (for example, `dashboard`), and up to 8192 characters of plain text. An omitted text value sends an empty string.

Set `RELAY_DISPLAY_URL` in the MCP server environment to the coordinator's origin. The default is `http://127.0.0.1:8766` for a separate process on the same Pi. Remote origins require HTTPS. If `RELAY_DISPLAY_TOKEN` is set, the tool sends it as a bearer token.

A request with a comparison prompt looks like this.

```http
PUT /v1/screens/1/state
Content-Type: application/json

{"template":"comparison","text":"I want to compare a 3060 Ti vs a 4060 Ti"}
```

For a template that supplies its own data, Relay can call `change_screen(1, "google_calendar_view")`. The kiosk receives `{"template":"google_calendar_view","text":""}`. The template IDs in these examples describe future layouts.

| Screen condition | Coordinator behavior |
| --- | --- |
| Known and connected | Forward to the active connection for that ID, then return HTTP 200 or 202 with `{"screen_id":1,"status":"accepted"}`. |
| Known and offline | Discard the request immediately and return HTTP 409. Reconnecting must never replay it. |
| Unknown ID | Return HTTP 404. |
| Delivery uncertain | Return an error. A timeout leaves the outcome unknown; the tool makes one attempt. |

## Suggested kiosk design

Run the coordinator as its own service alongside MCP. Give each kiosk an ID and a credential scoped to that ID. Screen 1 can run Chromium in kiosk mode on the Pi and load a screen-specific page from the display service. A future screen on a different computer can load its own page and connect outbound over WSS.

Keep a registry of active connections keyed by screen ID and remove disconnected clients. Forward commands only to the matching live socket. The kiosk maps template IDs to built-in layouts. Its calendar layout can later fetch calendar data, while its comparison layout can consume the prompt in `text`. Treat that field as plain text (`textContent` in a browser). To confirm rendering in a future version, have the kiosk return a separate acknowledgement after applying the layout.
