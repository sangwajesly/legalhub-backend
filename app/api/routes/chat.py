from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List
import uuid

from app.dependencies import get_current_user
from app.models.user import User
from app.services import firebase_service, langchain_service, file_service
from app.config import settings
from app.schemas.chat import (
    CreateSessionResponse,
    MessageRequest,
    MessageResponse,
    HistoryResponse,
    FeedbackRequest,
    ChatMessage as ChatMessageSchema,
)
from app.models.chat import (
    ChatMessage as ChatMessageModel,
)

# FIXED: Changed prefix from /api/chat to /api/v1/chat to match frontend
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(user: User = Depends(get_current_user)):
    """Create a new chat session for the authenticated user."""
    session_id = str(uuid.uuid4())
    try:
        await langchain_service.create_session(user.uid, session_id)
        return {"sessionId": session_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create chat session: {e}"
        )


@router.get("/sessions")
async def get_sessions(user: User = Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    try:
        sessions = await firebase_service.get_user_chat_sessions(user.uid)
        return {"sessions": sessions}
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        # Ensure items is always a list, even if empty, to prevent frontend TypeError
        return SessionsPaginatedResponse(items=[], total=0, page=page, size=size)


@router.delete("/sessions/{id}")
async def delete_session(id: str, user: Optional[dict] = Depends(get_current_user)):
    """Delete a chat session"""
    try:
        await firebase_service.delete_chat_session(id)
    except Exception:
        raise HTTPException(
            status_code=404, detail="Session not found or delete failed"
        )
    return {"ok": True}


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message_to_session(
    session_id: str,
    payload: MessageRequest,
    user: User = Depends(get_current_user)
):
    """Send a message to a specific session"""
    # Call LangChain service
    reply_text = await langchain_service.generate_response(
        session_id=session_id,
        user_id=user.uid,
        user_message=payload.message,
        attachments=payload.attachments if hasattr(
            payload, 'attachments') else None,
        history=payload.history if hasattr(payload, 'history') else None
    )

    return {"reply": reply_text, "sessionId": session_id}


@router.get("/sessions/{session_id}/messages", response_model=HistoryResponse)
async def get_session_messages(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user)
):
    """Get message history for a specific session"""
    try:
        chat_message_models: List[ChatMessageModel] = (
            await firebase_service.get_chat_history(session_id)
        )
        msgs = [
            ChatMessageSchema.model_validate(m.model_dump(by_alias=True)).model_dump(
                by_alias=True
            )
            for m in chat_message_models
        ]
    except Exception as e:
        print(f"Error getting chat history: {e}")
        msgs = []
    return {"messages": msgs}


@router.post("/sessions/{session_id}/messages/{message_id}/feedback")
async def submit_message_feedback(
    session_id: str,
    message_id: str,
    payload: FeedbackRequest,
    user: Optional[dict] = Depends(get_current_user)
):
    """Submit feedback for a specific message"""
    try:
        firebase_service.db.collection("chat_feedback").add(
            {
                "sessionId": session_id,
                "messageId": message_id,
                "userId": user.get("uid"),
                "rating": payload.rating,
                "feedback": payload.feedback,
            }
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Feedback submission failed: {str(e)}")


# Legacy endpoints for backward compatibility
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
        file_id = await file_service.file_service.save_upload(file)
        return {"fileId": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
