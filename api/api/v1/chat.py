from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.utils.types import ChatCompletionRequest
from api.core.llm_gateway import llm_gateway
from api.utils.logger import logger


router = APIRouter()


@router.post("/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    logger.info(f"Received chat completion request for model {request.model}")

    return StreamingResponse(
        llm_gateway.process_request(request),
        media_type="text/event-stream"
    )
