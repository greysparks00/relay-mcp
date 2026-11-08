"""Forward desired screen state to the separately deployed display coordinator."""

import asyncio
from http.client import HTTPConnection, HTTPException, HTTPSConnection
import json
import os
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import Field


def send_content(screen_id: int, content: str) -> dict:
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
        body = json.dumps({"id": screen_id, "content": content}, ensure_ascii=False).encode("utf-8")
        connection.request("POST", "/v1/screens/send", body, headers)
        response = connection.getresponse()
        if response.status == 409:
            raise ValueError(f"Screen {screen_id} is offline. The coordinator discarded the request.")
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
                or ack["id"] != screen_id or ack.get("status") != "accepted"):
            raise ValueError("Invalid display acknowledgement.")
        return {"id": screen_id, "status": ack["status"]}
    except (OSError, HTTPException) as error:
        raise ValueError("No acknowledgement from the display coordinator. Delivery is unconfirmed.") from error
    finally:
        connection.close()


async def change_screen(id: Annotated[int, Field(gt=0, le=2147483647)],
                        content: Annotated[str, Field(max_length=8192)] = "") -> dict:
    """Send literal content to a registered screen by ID. Content may be a view name such as dashboard, a free-form request, or empty. Offline requests are discarded."""
    return await asyncio.to_thread(send_content, id, content)
