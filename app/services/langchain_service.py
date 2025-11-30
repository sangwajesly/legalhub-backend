from typing import List, Optional
import asyncio
import logging
from datetime import datetime, UTC

from app.services import firebase_service, gemini_service
from app.config import settings
from app.models.chat import ChatMessage # Import ChatMessage

logger = logging.getLogger(__name__)


async def _build_context(session_id: Optional[str], max_messages: int = 10) -> List[str]:
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
        logger.warning("Failed to load chat history for session %s: %s", session_id, e)
        msgs = []

    parts: List[str] = []
    for m in msgs or []:
        # Ensure 'role' and 'text' are accessed from ChatMessage object
        parts.append(f"{m.role}: {m.text}")
    return parts


def _compose_prompt(context: List[str], user_message: str) -> str:
    system = (
        "You are LegalHub's assistant: provide concise, accurate legal information, "
        "explain legal terms in plain language, and when unsure, state that you are not a lawyer."
    )
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
        # Use the new create_chat_session function
        await firebase_service.create_chat_session(user_id, session_id)
    except Exception as e:
        logger.warning("Failed to create chat session %s for user %s: %s", session_id, user_id, e)


async def generate_response(session_id: Optional[str], user_id: Optional[str], user_message: str) -> str:
    """Generate a response for a user message using the Gemini adapter.

    This function builds a simple contextual prompt (last N messages + system prompt),
    calls `gemini_service.send_message`, and persists the assistant reply to Firestore.
    """
    # Persist user message first
    if session_id:
        user_chat_message = ChatMessage(
            role="user",
            text=user_message,
            userId=user_id,
            createdAt=datetime.now(UTC)
        )
        await firebase_service.add_chat_message(session_id, user_chat_message)

    context = await _build_context(session_id) # Await _build_context
    prompt = _compose_prompt(context, user_message)

    # Call gemini adapter (mocked in DEV by default)
    try:
        ai_result = await gemini_service.send_message(prompt)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        # Return a safe fallback message
        return "I'm sorry, I couldn't process that right now. Please try again later."

    # Normalize reply
    reply = None
    if isinstance(ai_result, dict):
        reply = ai_result.get("response") or ai_result.get("text") or str(ai_result.get("raw") or ai_result)
    else:
        reply = str(ai_result)

    if not reply:
        reply = ""

    # Persist assistant message
    if session_id:
        assistant_chat_message = ChatMessage(
            role="assistant",
            text=reply,
            userId=user_id, # Associate with the user who initiated the chat
            createdAt=datetime.now(UTC)
        )
        await firebase_service.add_chat_message(session_id, assistant_chat_message)

    return reply


async def generate_response_stream(session_id: Optional[str], user_id: Optional[str], user_message: str):
    """Async generator that yields response chunks from the LLM adapter.

    This yields raw text chunks as they become available and persists the final
    assistant reply to Firestore at the end.
    """
    # Persist user message first
    if session_id:
        user_chat_message = ChatMessage(
            role="user",
            text=user_message,
            userId=user_id,
            createdAt=datetime.now(UTC)
        )
        await firebase_service.add_chat_message(session_id, user_chat_message)

    context = await _build_context(session_id) # Await _build_context
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
    if session_id:
        assistant_chat_message = ChatMessage(
            role="assistant",
            text=final_reply,
            userId=user_id, # Associate with the user who initiated the chat
            createdAt=datetime.now(UTC)
        )
        await firebase_service.add_chat_message(session_id, assistant_chat_message)