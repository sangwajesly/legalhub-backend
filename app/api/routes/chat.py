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
from pydantic import BaseModel


class QueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[List[dict]] = None
    use_rag: bool = True
    top_k: int = 5

# FIXED: Changed prefix from /api/chat to /api/v1/chat to match frontend
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# In-memory storage fallback for demo/development mode when Firestore is unavailable
IN_MEMORY_SESSIONS = []
IN_MEMORY_MESSAGES = {}


def safe_iso_format(val):
    """Safely format a datetime or similar object to an ISO 8601 string"""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val) if val else None


def normalize_session_data(s: dict) -> dict:
    """Normalize a session dict to be fully serializable with camelCase keys"""
    if not isinstance(s, dict):
        return s
    
    normalized = {}
    for k, v in s.items():
        if k in ("createdAt", "lastMessageAt", "created_at", "last_message_at"):
            normalized[k] = safe_iso_format(v)
        else:
            normalized[k] = v
            
    # Ensure standard frontend keys are populated
    if "sessionId" not in normalized and "id" in normalized:
        normalized["sessionId"] = normalized["id"]
    elif "id" not in normalized and "sessionId" in normalized:
        normalized["id"] = normalized["sessionId"]
        
    return normalized


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(user: User = Depends(get_current_user)):
    """Create a new chat session for the authenticated user."""
    session_id = str(uuid.uuid4())
    try:
        await langchain_service.create_session(user.uid, session_id)
        return {"sessionId": session_id}
    except Exception as e:
        print(f"Error creating session in Firestore: {e}. Falling back to in-memory store.")
        from datetime import datetime, UTC
        new_session = {
            "sessionId": session_id,
            "id": session_id,
            "userId": user.uid,
            "title": "New Chat",
            "createdAt": safe_iso_format(datetime.now(UTC)),
            "lastMessageAt": safe_iso_format(datetime.now(UTC))
        }
        IN_MEMORY_SESSIONS.insert(0, new_session)
        IN_MEMORY_MESSAGES[session_id] = []
        return {"sessionId": session_id}


@router.get("/sessions")
async def get_sessions(user: User = Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    try:
        sessions = await firebase_service.get_user_chat_sessions(user.uid)
        normalized_sessions = [normalize_session_data(s) for s in sessions] if sessions else []
        
        if not normalized_sessions and IN_MEMORY_SESSIONS:
            return {"sessions": [normalize_session_data(s) for s in IN_MEMORY_SESSIONS]}
        return {"sessions": normalized_sessions}
    except Exception as e:
        print(f"Error fetching sessions: {e}. Falling back to in-memory store.")
        return {"sessions": [normalize_session_data(s) for s in IN_MEMORY_SESSIONS]}


@router.delete("/sessions/{id}")
async def delete_session(id: str, user: Optional[dict] = Depends(get_current_user)):
    """Delete a chat session"""
    try:
        await firebase_service.delete_chat_session(id)
    except Exception:
        # Fallback to in-memory
        global IN_MEMORY_SESSIONS
        IN_MEMORY_SESSIONS = [s for s in IN_MEMORY_SESSIONS if s.get("sessionId") != id]
        if id in IN_MEMORY_MESSAGES:
            del IN_MEMORY_MESSAGES[id]
    return {"ok": True}


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message_to_session(
    session_id: str,
    payload: MessageRequest,
    user: User = Depends(get_current_user)
):
    """Send a message to a specific session using the RAG pipeline."""
    from datetime import datetime, UTC

    # Update in-memory session timestamp / title
    for s in IN_MEMORY_SESSIONS:
        if s.get("sessionId") == session_id:
            s["lastMessageAt"] = datetime.now(UTC)
            s["title"] = payload.message[:30] + "..." if len(payload.message) > 30 else payload.message
            break

    # Store user message in memory
    if session_id not in IN_MEMORY_MESSAGES:
        IN_MEMORY_MESSAGES[session_id] = []
    IN_MEMORY_MESSAGES[session_id].append({
        "id": f"msg-user-{int(datetime.now(UTC).timestamp()*1000)}",
        "role": "user",
        "text": payload.message,
        "userId": user.uid,
        "createdAt": datetime.now(UTC)
    })

    # --- RAG Pipeline ---
    try:
        from app.services.rag_service import rag_service
        history = payload.history if hasattr(payload, 'history') else None
        reply_text, _docs = await rag_service.generate_rag_response(
            session_id=session_id,
            user_id=user.uid,
            user_message=payload.message,
            use_rag=True,
            top_k=5
        )
    except Exception as e:
        print(f"RAG pipeline failed: {e}. Falling back to direct AI provider call.")
        from app.services import ai_service
        try:
            result = await ai_service.send_message(payload.message)
            reply_text = result.get("response", str(result)) if isinstance(result, dict) else str(result)
        except Exception as ai_err:
            print(f"AI fallback also failed: {ai_err}.")
            reply_text = "I am here to assist you with Cameroonian law. Please ask any specific legal questions."

    # Store assistant message in memory
    IN_MEMORY_MESSAGES[session_id].append({
        "id": f"msg-bot-{int(datetime.now(UTC).timestamp()*1000)}",
        "role": "assistant",
        "text": reply_text,
        "userId": user.uid,
        "createdAt": datetime.now(UTC)
    })

    return {"reply": reply_text, "sessionId": session_id}


@router.post("/query")
async def stateless_query(
    payload: QueryRequest,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Stateless RAG query endpoint - works for guest users and authenticated users.
    Accepts message + optional history, returns a RAG-augmented response.
    """
    from app.services.rag_service import rag_service

    user_id = user.uid if user else "guest"
    session_id = payload.session_id  # May be None for guests

    try:
        reply_text, retrieved_docs = await rag_service.generate_rag_response(
            session_id=session_id,
            user_id=user_id,
            user_message=payload.message,
            use_rag=payload.use_rag,
            top_k=payload.top_k
        )
        return {
            "reply": reply_text,
            "sessionId": session_id,
            "sources": [
                {"source": d.get("source"), "score": round(d.get("score", 0), 3)}
                for d in retrieved_docs
            ]
        }
    except Exception as e:
        print(f"Stateless RAG query failed: {e}")
        from app.services import ai_service
        try:
            result = await ai_service.send_message(payload.message)
            reply_text = result.get("response", str(result)) if isinstance(result, dict) else str(result)
            return {"reply": reply_text, "sessionId": session_id, "sources": []}
        except Exception as ai_err:
            raise HTTPException(status_code=500, detail=f"Chat service unavailable: {ai_err}")


@router.get("/sessions/{session_id}/messages", response_model=HistoryResponse)
async def get_session_messages(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user)
):
    """Get message history for a specific session"""
    from datetime import datetime, UTC
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
        if not msgs and session_id in IN_MEMORY_MESSAGES:
            msgs = IN_MEMORY_MESSAGES[session_id]
    except Exception as e:
        print(f"Error getting chat history: {e}. Falling back to in-memory store.")
        msgs = IN_MEMORY_MESSAGES.get(session_id, [])
    
    # Normalize keys for ChatMessage schema (converting text -> text, role -> role)
    normalized_msgs = []
    for m in msgs:
        normalized_msgs.append({
            "id": m.get("id"),
            "role": m.get("role"),
            "text": m.get("text") or m.get("content") or "",
            "userId": m.get("userId") or m.get("user_id"),
            "createdAt": m.get("createdAt") or m.get("created_at") or datetime.now(UTC)
        })
    return {"messages": normalized_msgs}


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
