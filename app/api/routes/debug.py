from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional

from app.config import settings
from app.services import gemini_service

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.post("/gemini")
async def debug_gemini(message: str, stream: Optional[bool] = False):
    """Debug route to call Gemini directly. Only enabled in DEBUG mode."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Debug routes disabled")

    if stream:
        async def event_stream():
            yield ": debug stream open\n\n"
            async for chunk in gemini_service.stream_send_message(message):
                data = str(chunk.get("response") if isinstance(chunk, dict) else chunk)
                yield f"data: {data}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # Non-streaming
    result = await gemini_service.send_message(message)
    return result
