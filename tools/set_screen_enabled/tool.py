import asyncio
from typing import Annotated

from pydantic import Field

from tools._display import send_display_request


# Wake the numbered kiosk to show its current content (enabled=true) or put it on a
# black sleep screen (enabled=false). The monitor stays powered and connected.
async def set_screen_enabled(id: Annotated[int, Field(gt=0, le=2147483647)], enabled: bool) -> dict:
    return await asyncio.to_thread(send_display_request, id, {"enabled": enabled}, "applied")
