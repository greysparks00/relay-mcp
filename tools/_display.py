from http.client import HTTPConnection, HTTPException, HTTPSConnection
import json
import os
from urllib.parse import urlsplit


def send_display_request(screen_id: int, payload: dict, expected_status: str) -> dict:
    url = urlsplit(os.environ.get("RELAY_DISPLAY_URL") or "http://127.0.0.1:8766")
    if (url.scheme not in {"http", "https"} or not url.hostname or url.username is not None
            or url.password is not None or url.query or url.fragment or url.path not in {"", "/"}):
        raise ValueError("RELAY_DISPLAY_URL must be an HTTP(S) origin.")

    if url.scheme == "http" and url.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("Use HTTPS for a remote display coordinator, or use a loopback tunnel.")

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    if token := os.environ.get("RELAY_DISPLAY_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    connection = (HTTPSConnection if url.scheme == "https" else HTTPConnection)(url.hostname, url.port, timeout=5)
    try:
        body = json.dumps({"id": screen_id, **payload}, ensure_ascii=False).encode("utf-8")
        connection.request("POST", "/v1/screens/send", body, headers)
        response = connection.getresponse()

        if response.status == 409:
            raise ValueError(f"Screen {screen_id} is offline. The coordinator discarded the request.")

        if response.status == 504:
            raise ValueError("The kiosk did not confirm the command. Delivery is unconfirmed.")

        if response.status == 404:
            raise ValueError(f"The coordinator does not recognize screen {screen_id}.")

        if response.status in {401, 403}:
            raise ValueError("The display coordinator rejected Relay's credentials.")

        if response.status not in {200, 202}:
            raise ValueError(f"The display coordinator returned HTTP {response.status}.")

        raw = response.read(4097)

        if len(raw) > 4096:
            raise ValueError("Oversized display acknowledgement.")

        ack = json.loads(raw)

        if (not isinstance(ack, dict) or type(ack.get("id")) is not int
                or ack["id"] != screen_id or ack.get("status") != expected_status):

            raise ValueError("Invalid display acknowledgement.")

        return {"id": screen_id, "status": ack["status"]}

    except (OSError, HTTPException) as error:

        raise ValueError("No acknowledgement from the display coordinator. Delivery is unconfirmed.") from error
    finally:
        connection.close()
