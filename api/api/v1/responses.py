import json
from typing import Any


def create_sse_event(data: Any) -> str:
    if data == "[DONE]":
        return "data: [DONE]\n\n"

    payload = json.dumps(data.model_dump(exclude_none=True))
    return f"data: {payload}\n\n"
