from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., alias="sessionId")

    model_config = ConfigDict(populate_by_name=True)


class MessageRequest(BaseModel):
    session_id: Optional[str] = Field(None, alias="sessionId")
    message: str
    attachments: List[str] = []
    history: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Optional chat history for stateless context. Format: [{'role': 'user', 'text': '...'}]"
    )

    model_config = ConfigDict(populate_by_name=True)


class RetrievedDocument(BaseModel):
    """Schema for a retrieved document from RAG"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class MessageResponse(BaseModel):
    reply: str
    session_id: str = Field(..., alias="sessionId")
    retrieved_documents: Optional[List[RetrievedDocument]] = None

    model_config = ConfigDict(populate_by_name=True)


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str
    text: str
    user_id: Optional[str] = Field(None, alias="userId")
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class HistoryResponse(BaseModel):
    messages: List[ChatMessage]


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    message_id: str = Field(..., alias="messageId")
    rating: int = 0

    model_config = ConfigDict(populate_by_name=True)
