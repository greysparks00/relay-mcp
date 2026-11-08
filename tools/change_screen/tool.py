# Forward desired screen state to the separately deployed display coordinator.

import asyncio
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from tools._display import send_display_request

DisplayText = Annotated[str, Field(max_length=8192)]


class TextScreen(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["text"]
    content: DisplayText


class ComparisonScreen(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["comparison"]
    option1: Annotated[str, Field(min_length=1, max_length=8192)]
    option2: Annotated[str, Field(min_length=1, max_length=8192)]


# Choose text for explanations or messages, comparison for two alternatives. Use
# {"type":"text","content":"..."} or {"type":"comparison","option1":"...","option2":"..."}.
# Fill the fields with display-ready answers on any topic and name each alternative.
async def change_screen(id: Annotated[int, Field(gt=0, le=2147483647)],
                        screen: TextScreen | ComparisonScreen) -> dict:
    return await asyncio.to_thread(send_display_request, id, {"screen": screen.model_dump()}, "accepted")
