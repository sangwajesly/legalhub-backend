from typing import List, Optional
import asyncio

from app.services import firebase_service, gemini_service
from app.config import settings


def _build_context(session_id: Optional[str], max_messages: int = 10) -> List[str]:
    """Load the last N messages from Firestore and return as list of strings.

    This is a minimal 'LangChain-like' context builder for MVP. For Phase 2
    we can replace this with a full LangChain `ConversationBufferMemory` and
    an LLM wrapper for Gemini.
    """
    if not session_id:
        return []
    try:
        msgs = firebase_service.get_chat_history(session_id, limit=max_messages)
    except Exception:
        msgs = []

    parts: List[str] = []
    for m in msgs:
        role = m.get("role") or m.get("sender") or "user"
        text = m.get("text") or m.get("message") or ""
        parts.append(f"{role}: {text}")
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
    firebase_service.save_chat_session(user_id, session_id, {})


async def generate_response(session_id: Optional[str], user_id: Optional[str], user_message: str) -> str:
    """Generate a response for a user message using the Gemini adapter.

    This function builds a simple contextual prompt (last N messages + system prompt),
    calls `gemini_service.send_message`, and persists the assistant reply to Firestore.
    """
    context = _build_context(session_id)
    prompt = _compose_prompt(context, user_message)

    # Call gemini adapter (mocked in DEV by default)
    ai_result = await gemini_service.send_message(prompt)
    if isinstance(ai_result, dict):
        reply = ai_result.get("response") or ai_result.get("text") or str(ai_result)
    else:
        reply = str(ai_result)

    # Persist messages
    try:
        if session_id:
            firebase_service.append_message(session_id, {"role": "assistant", "text": reply})
    except Exception:
        # swallow persistence errors in DEV mode
        pass

    return reply
