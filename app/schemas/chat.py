from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class CreateSessionResponse(BaseModel):
    sessionId: str


class MessageRequest(BaseModel):
    sessionId: Optional[str] = None
    message: str
    attachments: List[str] = []


class RetrievedDocument(BaseModel):
    """Schema for a retrieved document from RAG"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class MessageResponse(BaseModel):
    reply: str
    sessionId: str
    retrieved_documents: Optional[List[RetrievedDocument]] = None


class ChatMessage(BaseModel):
    id: Optional[str]
    role: str
    text: str
    userId: Optional[str]
    createdAt: Optional[datetime]


class HistoryResponse(BaseModel):
    messages: List[ChatMessage]


class FeedbackRequest(BaseModel):
    sessionId: str
    messageId: str
    rating: int = 0
