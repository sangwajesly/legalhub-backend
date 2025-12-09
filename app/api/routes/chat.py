from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List
import uuid

from app.dependencies import get_current_user
from app.dependencies import get_current_user
from app.services import firebase_service, langchain_service, file_service
from app.config import settings
from app.schemas.chat import (
    CreateSessionResponse,
    MessageRequest,
    MessageResponse,
    HistoryResponse,
    FeedbackRequest,
    ChatMessage as ChatMessageSchema,  # Import ChatMessage from schemas for response
)
from app.models.chat import (
    ChatMessage as ChatMessageModel,
)  # Import ChatMessage from models for internal use


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(user: Optional[dict] = Depends(get_current_user)):
    """Create a new chat session for the authenticated user."""
    session_id = str(uuid.uuid4())
    await langchain_service.create_session(user.get("uid"), session_id)
    return {"sessionId": session_id}


@router.post("", response_model=CreateSessionResponse)
async def create_new_chat(user: Optional[dict] = Depends(get_current_user)):
    """Create a new chat session (alias for /session to support frontend)"""
    return await create_session(user)


@router.get("/sessions")
async def get_sessions(user: Optional[dict] = Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    try:
        sessions = await firebase_service.get_user_chat_sessions(user.get("uid"))
        return {"sessions": sessions}
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return {"sessions": []}


@router.delete("/session/{id}")
async def delete_session(id: str, user: Optional[dict] = Depends(get_current_user)):
    try:
        await firebase_service.delete_chat_session(id)  # Await the async function
    except Exception:
        raise HTTPException(
            status_code=404, detail="Session not found or delete failed"
        )
    return {"ok": True}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Upload a file for chat context.
    Returns: {"fileId": "..."}
    """
    try:
        # Save file using FileService
        file_id = await file_service.file_service.save_upload(file)
        return {"fileId": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/message", response_model=MessageResponse)
async def send_message(
    payload: MessageRequest, user: Optional[dict] = Depends(get_current_user)
):
    # create session if missing
    session_id = payload.sessionId or str(uuid.uuid4())
    if not payload.sessionId:
        await langchain_service.create_session(user.get("uid"), session_id)

    # call LangChain service
    reply_text = await langchain_service.generate_response(
        session_id=session_id, 
        user_id=user.get("uid"), 
        user_message=payload.message,
        attachments=payload.attachments
    )

    return {"reply": reply_text, "sessionId": session_id}


@router.get("/history", response_model=HistoryResponse)
async def get_history(sessionId: str, user: Optional[dict] = Depends(get_current_user)):
    try:
        # Get ChatMessageModel objects from firebase_service
        chat_message_models: List[ChatMessageModel] = (
            await firebase_service.get_chat_history(sessionId)
        )
        # Convert ChatMessageModel objects to ChatMessageSchema dictionaries for the response
        msgs = [
            ChatMessageSchema.model_validate(m.model_dump(by_alias=True)).model_dump(
                by_alias=True
            )
            for m in chat_message_models
        ]
    except Exception as e:
        # Log the error for debugging
        print(f"Error getting chat history: {e}")
        msgs = []
    return {"messages": msgs}


@router.post("/feedback")
async def feedback(
    payload: FeedbackRequest, user: Optional[dict] = Depends(get_current_user)
):
    # store feedback in a collection
    try:
        # Corrected: Use firebase_service.db directly
        firebase_service.db.collection("chat_feedback").add(
            {
                "sessionId": payload.sessionId,
                "messageId": payload.messageId,
                "rating": payload.rating,
            }
        )
    except Exception:
        pass
    return {"ok": True}


@router.post("/message/stream")
async def send_message_stream(
    payload: MessageRequest, user: Optional[dict] = Depends(get_current_user)
):
    """Stream the AI response back to the client using Server-Sent Events (SSE).

    The client should connect and parse `text/event-stream` messages. Each
    chunk is sent as an `data: ...` SSE event.
    """
    session_id = payload.sessionId or str(uuid.uuid4())
    if not payload.sessionId:
        await langchain_service.create_session(user.get("uid"), session_id)

    async def event_stream():
        # yield initial comment to establish the stream
        yield ": stream open\n\n"
        async for chunk in langchain_service.generate_response_stream(
            session_id=session_id, user_id=user.get("uid"), user_message=payload.message
        ):
            # Format as SSE
            # Escape newlines in chunk data
            if chunk is None:
                continue
            data = str(chunk).replace("\n", "\ndata: ")
            yield f"data: {data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
