from typing import List, Optional, Dict, Any
import asyncio
from fastapi import HTTPException
import logging
from datetime import datetime, UTC

from app.services import firebase_service, gemini_service, file_service
from app.services.pdf_ingestion_service import extract_text_from_pdf
import mimetypes
import base64
from app.config import settings
from app.models.chat import ChatMessage  # Import ChatMessage
from app.prompts import LEGALHUB_CORE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Lazy import RAG service to avoid circular imports
_rag_service = None


def get_rag_service():
    """Get or initialize the RAG service."""
    global _rag_service
    if _rag_service is None:
        from app.services.rag_service import rag_service
        _rag_service = rag_service
    return _rag_service


async def _build_context(
    session_id: Optional[str], max_messages: int = 10
) -> List[str]:
    """Load the last N messages from Firestore and return as list of strings.

    This is a minimal 'LangChain-like' context builder for MVP. For Phase 2
    we can replace this with a full LangChain `ConversationBufferMemory` and
    an LLM wrapper for Gemini.
    """
    if not session_id:
        return []
    try:
        # Use the updated get_chat_history which returns ChatMessage objects
        msgs: List[ChatMessage] = await firebase_service.get_chat_history(session_id)
        # Limit the number of messages for context
        msgs = msgs[-max_messages:]
    except Exception as e:
        logger.warning(
            "Failed to load chat history for session %s: %s", session_id, e)
        msgs = []

    parts: List[str] = []
    for m in msgs or []:
        # Ensure 'role' and 'text' are accessed from ChatMessage object
        parts.append(f"{m.role}: {m.text}")
    return parts


def _compose_prompt(context: List[str], user_message: str) -> str:
    system = LEGALHUB_CORE_SYSTEM_PROMPT
    prompt_parts = [f"System: {system}"]
    if context:
        prompt_parts.append("Conversation so far:")
        prompt_parts.extend(context)
    prompt_parts.append(f"User: {user_message}")
    prompt_parts.append("Assistant:")
    return "\n".join(prompt_parts)


async def create_session(user_id: str, session_id: str):
    """Create a new chat session in Firestore."""
    try:
        await firebase_service.create_chat_session(user_id, session_id)
        logger.info("Chat session %s created for user %s.",
                    session_id, user_id)
    except Exception as e:
        logger.error(
            "Failed to create chat session %s for user %s: %s", session_id, user_id, e
        )
        raise  # Re-raise the exception to propagate to the calling endpoint


async def _validate_chat_session(session_id: str, user_id: str):
    """
    Validates if a chat session exists and belongs to the authenticated user.
    Raises HTTPException if not valid.
    """
    session = await firebase_service.get_chat_session(session_id)  # Need to add this to firebase_service
    if not session:
        raise HTTPException(
            status_code=404, detail="Chat session not found."
        )
    # Assuming userId is stored in the chat session document
    if session.get("userId") != user_id:
        raise HTTPException(
            status_code=403, detail="Unauthorized to access this chat session."
        )


async def generate_response(
    session_id: Optional[str],
    user_id: Optional[str],
    user_message: str,
    attachments: Optional[List[str]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Generate a response for a user message using the Gemini adapter.

    If `history` is provided (stateless mode), it uses that context.
    Otherwise, it fetches history from Firestore using `session_id`.
    """
    print(
        f"DEBUG CHAT: user_id={user_id}, session_id={session_id}, has_history={bool(history)}")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated.")

    # 1. Attempt to validate session if provided
    has_session = False
    if session_id:
        try:
            await _validate_chat_session(session_id, user_id)
            has_session = True
        except HTTPException as e:
            if not history:
                raise e
            logger.warning(
                f"Session {session_id} not found or unauthorized, but history provided. Using stateless mode.")

    # 2. Context Building: Prefer provided history, fallback to DB
    context = []
    if history:
        for msg in history:
            role = msg.get("role", "unknown")
            text = msg.get("text", "")
            context.append(f"{role}: {text}")
    elif has_session and session_id:
        context = await _build_context(session_id)
    else:
        if not session_id:
            raise HTTPException(
                status_code=400, detail="Either sessionId or history must be provided.")

    # 3. Persist user message only if we have a valid session
    if has_session and session_id:
        try:
            user_chat_message = ChatMessage(
                role="user", text=user_message, userId=user_id, createdAt=datetime.now(UTC)
            )
            await firebase_service.add_chat_message(session_id, user_chat_message)
        except Exception as e:
            logger.error(f"Failed to persist user message to DB: {e}")

    # Process Attachments
    images_for_gemini = []
    doc_text = ""

    if attachments:
        for file_id in attachments:
            path = file_service.file_service.get_file_path(file_id)
            if not path:
                continue

            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                continue

            if mime_type.startswith("image/"):
                # Prepare for Gemini
                content = path.read_bytes()
                b64_data = base64.b64encode(content).decode('utf-8')
                images_for_gemini.append(
                    {"mime_type": mime_type, "data": b64_data})

            elif mime_type == "application/pdf":
                # Extract text
                text = extract_text_from_pdf(str(path))
                # Limit size
                doc_text += f"\n[Attached PDF Content]:\n{text[:5000]}..."

            elif mime_type.startswith("text/"):
                text = path.read_text(encoding='utf-8', errors='ignore')
                doc_text += f"\n[Attached Text Content]:\n{text[:5000]}..."

    # Append doc content to message
    full_message = user_message
    if doc_text:
        full_message += f"\n\n--- Referenced Documents ---\n{doc_text}"

    prompt = _compose_prompt(context, full_message)

    # Call gemini adapter (mocked in DEV by default)
    try:
        # Pass images if available
        ai_result = await gemini_service.send_message(prompt, images=images_for_gemini)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        # Return a safe fallback message
        return "I'm sorry, I couldn't process that right now. Please try again later."

    # Normalize reply
    reply = None
    if isinstance(ai_result, dict):
        reply = (
            ai_result.get("response")
            or ai_result.get("text")
            or str(ai_result.get("raw") or ai_result)
        )
    else:
        reply = str(ai_result)

    if not reply:
        reply = ""

    final_parts: List[str] = []

    # Assistant persistence logic
    if has_session and session_id:
        try:
            assistant_chat_message = ChatMessage(
                role="assistant",
                text=reply,
                userId=user_id,
                createdAt=datetime.now(UTC),
            )
            await firebase_service.add_chat_message(session_id, assistant_chat_message)
        except Exception as e:
            logger.error(f"Failed to persist assistant message to DB: {e}")

    return reply


async def generate_response_stream(
    session_id: Optional[str],
    user_id: Optional[str],
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None
):
    """Async generator that yields response chunks from the LLM adapter.

    This yields raw text chunks as they become available and persists the final
    assistant reply to Firestore at the end.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated.")

    # 1. Attempt to validate session if provided
    has_session = False

    if session_id:
        try:
            await _validate_chat_session(session_id, user_id)
            has_session = True
        except HTTPException as e:
            if not history:
                raise e
            logger.warning(
                f"Session {session_id} not found or unauthorized, but history provided. Using stateless mode.")

    # 2. Context Building: Prefer provided history, fallback to DB
    context = []
    if history:
        for msg in history:
            role = msg.get("role", "unknown")
            text = msg.get("text", "")
            context.append(f"{role}: {text}")
    elif has_session and session_id:
        context = await _build_context(session_id)  # Await _build_context
    else:
        if not session_id:
            raise HTTPException(
                status_code=400, detail="Either sessionId or history must be provided.")

    # 3. Persist user message only if we have a valid session
    if has_session and session_id:
        try:
            user_chat_message = ChatMessage(
                role="user", text=user_message, userId=user_id, createdAt=datetime.now(UTC)
            )
            await firebase_service.add_chat_message(session_id, user_chat_message)
        except Exception as e:
            logger.error(f"Failed to persist user message to DB: {e}")

    prompt = _compose_prompt(context, user_message)

    final_parts: List[str] = []

    try:
        async for chunk in gemini_service.stream_send_message(prompt):
            text = ""
            if isinstance(chunk, dict):
                text = chunk.get("response") or ""
            else:
                text = str(chunk)
            final_parts.append(text)
            yield text
    except Exception as e:
        logger.exception("Streaming LLM call failed: %s", e)
        # yield a final error fragment and stop
        yield ""

    final_reply = "".join(final_parts)
    # Persist final assembled reply
    if has_session and session_id:
        try:
            assistant_chat_message = ChatMessage(
                role="assistant",
                text=final_reply,
                userId=user_id,
                createdAt=datetime.now(UTC),
            )
            await firebase_service.add_chat_message(session_id, assistant_chat_message)
        except Exception as e:
            logger.error(
                f"Failed to persist final streaming message to DB: {e}")


# ============================================
# RAG-ENHANCED ENDPOINTS
# ============================================

async def generate_rag_response(
    session_id: Optional[str],
    user_id: Optional[str],
    user_message: str,
    use_rag: bool = True,
    top_k: int = 3
) -> tuple:
    """
    Generate a response with RAG augmentation.

    Args:
        session_id: Chat session ID
        user_id: User ID
        user_message: User's message
        use_rag: Whether to use RAG enhancement
        top_k: Number of top documents to retrieve

    Returns:
        Tuple of (response_text, retrieved_documents)
    """
    rag_service = get_rag_service()
    return await rag_service.generate_rag_response(
        session_id=session_id,
        user_id=user_id,
        user_message=user_message,
        use_rag=use_rag,
        top_k=top_k
    )


async def generate_rag_response_stream(
    session_id: Optional[str],
    user_id: Optional[str],
    user_message: str,
    use_rag: bool = True,
    top_k: int = 3
):
    """
    Stream a RAG-augmented response.

    Yields response chunks as they become available.
    """
    rag_service = get_rag_service()
    async for chunk in rag_service.generate_rag_response_stream(
        session_id=session_id,
        user_id=user_id,
        user_message=user_message,
        use_rag=use_rag,
        top_k=top_k
    ):
        yield chunk
